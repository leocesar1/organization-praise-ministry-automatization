import io
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

# Bitrates a tentar em ordem decrescente de qualidade
COMPRESSION_BITRATES_KBPS = [128, 96, 64, 48]

# Limite alvo em bytes (48 MB com margem de segurança)
DEFAULT_TARGET_SIZE_BYTES = 48 * 1024 * 1024


def _ffmpeg_available() -> bool:
    """Verifica se o ffmpeg está disponível no PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def compress_audio(content: bytes, filename: str, target_size_bytes: int = DEFAULT_TARGET_SIZE_BYTES) -> bytes:
    """
    Comprime um arquivo de áudio MP3 progressivamente até caber no limite de tamanho.

    Tenta os bitrates em sequência: 128kbps → 96kbps → 64kbps → 48kbps.
    Lança RuntimeError se nenhum bitrate conseguir reduzir o arquivo ao tamanho alvo.

    Args:
        content: Bytes do arquivo de áudio original.
        filename: Nome do arquivo (usado para logging e extensão).
        target_size_bytes: Tamanho máximo desejado em bytes (padrão: 48 MB).

    Returns:
        Bytes do arquivo comprimido.
    """
    if not _ffmpeg_available():
        raise RuntimeError(
            "ffmpeg não está disponível no PATH. "
            "Instale com: brew install ffmpeg"
        )

    original_size_mb = len(content) / 1024 / 1024
    logger.info(
        f"🗜️ Comprimindo '{filename}' ({original_size_mb:.1f} MB) para caber em "
        f"{target_size_bytes / 1024 / 1024:.0f} MB..."
    )

    for bitrate in COMPRESSION_BITRATES_KBPS:
        compressed = _compress_to_bitrate(content, bitrate)
        compressed_size_mb = len(compressed) / 1024 / 1024

        if len(compressed) <= target_size_bytes:
            logger.info(
                f"✅ '{filename}' comprimido com {bitrate}kbps: "
                f"{original_size_mb:.1f} MB → {compressed_size_mb:.1f} MB"
            )
            return compressed

        logger.warning(
            f"⚠️ '{filename}' ainda grande com {bitrate}kbps ({compressed_size_mb:.1f} MB). "
            f"Tentando bitrate menor..."
        )

    raise RuntimeError(
        f"Impossível comprimir '{filename}' abaixo de "
        f"{target_size_bytes / 1024 / 1024:.0f} MB mesmo com {COMPRESSION_BITRATES_KBPS[-1]}kbps."
    )


def _compress_to_bitrate(content: bytes, bitrate_kbps: int) -> bytes:
    """
    Usa ffmpeg via subprocess para reencoder o áudio no bitrate especificado.
    Toda a operação ocorre em memória (stdin/stdout) sem gravar em disco.
    """
    cmd = [
        "ffmpeg",
        "-y",                          # sobrescreve sem perguntar
        "-i", "pipe:0",                # lê da stdin
        "-vn",                         # remove vídeo/capa
        "-acodec", "libmp3lame",       # codec MP3
        "-b:a", f"{bitrate_kbps}k",   # bitrate alvo
        "-f", "mp3",                   # formato de saída
        "pipe:1",                      # escreve na stdout
    ]

    result = subprocess.run(
        cmd,
        input=content,
        capture_output=True,
        timeout=120,  # 2 minutos por arquivo
    )

    if result.returncode != 0:
        stderr_msg = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg falhou (código {result.returncode}): {stderr_msg[-500:]}")

    return result.stdout


def compress_files_to_fit(
    files: dict[str, bytes],
    max_total_bytes: int = DEFAULT_TARGET_SIZE_BYTES,
) -> dict[str, bytes]:
    """
    Recebe um dicionário {nome: bytes} e comprime os arquivos que precisam
    para que o total caiba dentro do limite.

    Estratégia:
      1. Se o total já cabe → retorna sem modificar.
      2. Caso contrário, comprime progressivamente todos os arquivos
         até que o total caiba ou até esgotar os bitrates disponíveis.

    Args:
        files: Dicionário {filename: content_bytes}.
        max_total_bytes: Limite total máximo em bytes.

    Returns:
        Dicionário com os arquivos (possivelmente comprimidos).
    """
    total = sum(len(v) for v in files.values())
    total_mb = total / 1024 / 1024

    if total <= max_total_bytes:
        logger.debug(f"Total de áudios ({total_mb:.1f} MB) está dentro do limite. Sem compressão necessária.")
        return files

    logger.warning(
        f"⚠️ Total de áudios ({total_mb:.1f} MB) excede o limite de "
        f"{max_total_bytes / 1024 / 1024:.0f} MB. Iniciando compressão..."
    )

    # Tenta cada bitrate até o total caber
    for bitrate in COMPRESSION_BITRATES_KBPS:
        logger.info(f"🗜️ Tentando compressão com {bitrate}kbps em todos os arquivos...")
        compressed_files = {}

        for filename, content in files.items():
            original_size_mb = len(content) / 1024 / 1024
            try:
                compressed = _compress_to_bitrate(content, bitrate)
                compressed_size_mb = len(compressed) / 1024 / 1024
                logger.info(
                    f"   '{filename}': {original_size_mb:.1f} MB → {compressed_size_mb:.1f} MB ({bitrate}kbps)"
                )
                compressed_files[filename] = compressed
            except RuntimeError as e:
                logger.error(f"Erro ao comprimir '{filename}': {e}")
                # Mantém o original se não conseguir comprimir
                compressed_files[filename] = content

        new_total = sum(len(v) for v in compressed_files.values())
        new_total_mb = new_total / 1024 / 1024

        if new_total <= max_total_bytes:
            logger.info(
                f"✅ Compressão bem-sucedida com {bitrate}kbps. "
                f"Total: {total_mb:.1f} MB → {new_total_mb:.1f} MB"
            )
            return compressed_files

        logger.warning(
            f"⚠️ Total ainda grande com {bitrate}kbps ({new_total_mb:.1f} MB). Tentando bitrate menor..."
        )

    # Retorna a melhor tentativa (com menor bitrate) mesmo que exceda
    logger.error(
        f"❌ Não foi possível comprimir os áudios abaixo de "
        f"{max_total_bytes / 1024 / 1024:.0f} MB mesmo com {COMPRESSION_BITRATES_KBPS[-1]}kbps. "
        f"Enviando com o menor bitrate disponível."
    )
    return compressed_files
