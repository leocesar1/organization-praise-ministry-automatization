import re
from dataclasses import dataclass
from core.models import MusicMetadata

@dataclass
class ReaperRegion:
    id: int
    name: str
    start_seconds: float
    end_seconds: float = 0.0

def parse_rpp_regions(rpp_content: str) -> list[ReaperRegion]:
    """
    Parseia o conteúdo de um arquivo .rpp para extrair as regiões.
    As regiões no Reaper são identificadas por linhas que começam com 'MARKER'
    onde o campo flags tem o bit 0 ativo (número ímpar, ex: 1, 9).
    """
    # Regex para capturar: MARKER <id> <pos> <name> <flags>
    # Aceita nomes entre aspas ou sem aspas
    marker_pattern = re.compile(
        r'^\s*MARKER\s+(\d+)\s+([\d.]+)\s+(?:"([^"]*)"|([^\s]+))\s+(\d+)',
        re.MULTILINE
    )
    
    starts = {}
    ends = {}
    
    for match in marker_pattern.finditer(rpp_content):
        r_id = int(match.group(1))
        r_pos = float(match.group(2))
        r_name = match.group(3) if match.group(3) is not None else match.group(4)
        r_flags = int(match.group(5))
        
        # Verifica se o bit 0 está ativo (flags é ímpar), indicando que é uma região
        if r_flags & 1:
            if r_name == "":
                # Fim da região
                ends[r_id] = r_pos
            else:
                # Início da região
                starts[r_id] = (r_name, r_pos)
                
    regions = []
    for r_id, (name, start) in starts.items():
        end = ends.get(r_id, start) # Fallback para o próprio início se não achar fim
        regions.append(ReaperRegion(id=r_id, name=name, start_seconds=start, end_seconds=end))
        
    # Ordena as regiões por tempo de início
    regions.sort(key=lambda r: r.start_seconds)
    return regions

def format_arrangement_message(metadata: MusicMetadata, regions: list[ReaperRegion]) -> str:
    """
    Formata o mapa de arranjo em MarkdownV2 para o Telegram.
    """
    def escape(text: str) -> str:
        if not text:
            return ""
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text

    # Nome limpo da música, artista e metadados
    msg = f"🎵 *{escape(metadata.name)}*\n"
    msg += f"🎤 _{escape(metadata.artist)}_\n"
    
    bpm_text = f"{metadata.bpm} BPM" if metadata.bpm > 0 else "0 BPM"
    msg += f"🔑 Tom: *{escape(metadata.key)}* \\| ⏱ *{escape(bpm_text)}* \\| 🎼 Compasso: *{escape(metadata.compass)}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "📋 *Estrutura / Arranjo:*\n"
    
    for r in regions:
        minutos = int(r.start_seconds) // 60
        segundos = int(r.start_seconds) % 60
        time_str = f"{minutos:02d}:{segundos:02d}"
        msg += f"`{time_str}` {escape(r.name)}\n"
        
    if regions:
        # A duração total é o fim da última região
        total_seconds = regions[-1].end_seconds
        tot_min = int(total_seconds) // 60
        tot_seg = int(total_seconds) % 60
        msg += f"\n*\\(Duração Total: {tot_min:02d}:{tot_seg:02d}\\)*"
        
    return msg
