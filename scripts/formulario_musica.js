// Formulário para Atualização de Música (macOS, JavaScript for Automation).
//
// Execução:   osascript -l JavaScript scripts/formulario_musica.js '<json_musicas>'
//             ou lendo via variável/argumento
// Saída:      JSON {"folder_id": "...", "name": "...", "confirmado": true} se confirmado; vazio se cancelado.

ObjC.import('Cocoa');

const app = $.NSApplication.sharedApplication;
app.setActivationPolicy($.NSApplicationActivationPolicyRegular);

function criarIconeMusica() {
  try {
    const cfgSize = $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(52, $.NSFontWeightRegular);
    const cfgColor = $.NSImageSymbolConfiguration.configurationWithHierarchicalColor($.NSColor.systemIndigoColor);
    const cfg = cfgSize.configurationByApplyingConfiguration(cfgColor);
    return $.NSImage.imageWithSystemSymbolNameAccessibilityDescription('music.note.list', 'Atualizar Música')
                    .imageWithSymbolConfiguration(cfg);
  } catch (e) {
    return null;
  }
}

function lerArquivo(caminho) {
  try {
    const nsStr = $.NSString.stringWithContentsOfFileEncodingError($(caminho), $.NSUTF8StringEncoding, null);
    return ObjC.unwrap(nsStr);
  } catch (e) {
    return null;
  }
}

function lerEntradaMusicas() {
  try {
    const args = $.NSProcessInfo.processInfo.arguments;
    for (let i = 0; i < args.count; i++) {
      const arg = ObjC.unwrap(args.objectAtIndex(i));
      if (!arg) continue;
      
      const limpo = arg.trim();
      // Se for caminho para arquivo .json
      if (limpo.endsWith('.json')) {
        const conteudo = lerArquivo(limpo);
        if (conteudo) {
          return JSON.parse(conteudo);
        }
      }
      
      // Se for JSON direto na string
      if (limpo.startsWith('[')) {
        return JSON.parse(limpo);
      }
    }
  } catch (e) {
    // Falha ao ler argumento ou arquivo
  }
  return [];
}

function prepararJanelaPrimeiroPlano(alert) {
  try {
    const win = alert.window;
    // NSScreenSaverWindowLevel (nível 1000): nível mais alto do gerenciador de janelas do macOS
    win.level = $.NSScreenSaverWindowLevel;
    win.collectionBehavior = $.NSWindowCollectionBehaviorCanJoinAllSpaces | $.NSWindowCollectionBehaviorStationary;
    win.hidesOnDeactivate = false;
    win.orderFrontRegardless;

    // O NSAlert.runModal às vezes redefine o window level para modal standard logo após abrir.
    // Usamos um NSTimer no loop principal para forçar e cravar o level alto assim que o modal subir.
    $.NSTimer.scheduledTimerWithTimeIntervalRepeatsBlock(0.05, false, function () {
      try {
        win.level = $.NSScreenSaverWindowLevel;
        win.orderFrontRegardless;
        app.activateIgnoringOtherApps(true);
      } catch (err) {}
    });
  } catch (e) {
    // Fallback caso ocorra erro
  }
  app.activateIgnoringOtherApps(true);
}

function selecionarMusica(musicas) {
  if (!musicas || musicas.length === 0) {
    const alertVazio = $.NSAlert.alloc.init;
    alertVazio.messageText = 'Nenhuma música encontrada';
    alertVazio.informativeText = 'Não foi possível carregar a lista de músicas do OneDrive.';
    const icone = criarIconeMusica();
    if (icone && icone.isValid) alertVazio.icon = icone;
    alertVazio.addButtonWithTitle('OK');
    prepararJanelaPrimeiroPlano(alertVazio);
    alertVazio.runModal;
    return null;
  }

  const alert = $.NSAlert.alloc.init;
  alert.messageText = 'Atualizar Música no Telegram';
  alert.informativeText = 'Selecione a música que deseja atualizar. Isso sincronizará os novos áudios e o mapa de arranjo (.rpp).';

  const icone = criarIconeMusica();
  if (icone && icone.isValid) alert.icon = icone;

  alert.addButtonWithTitle('Continuar');
  alert.addButtonWithTitle('Cancelar');

  const larguraPainel = 460;
  const alturaPainel = 70;
  const painel = $.NSView.alloc.initWithFrame($.NSMakeRect(0, 0, larguraPainel, alturaPainel));

  // Rótulo
  const lbl = $.NSTextField.alloc.initWithFrame($.NSMakeRect(0, 42, larguraPainel, 20));
  lbl.stringValue = 'Música disponível:';
  lbl.bezeled = false;
  lbl.drawsBackground = false;
  lbl.editable = false;
  lbl.selectable = false;
  painel.addSubview(lbl);

  // Popup com títulos
  const popup = $.NSPopUpButton.alloc.initWithFramePullsDown($.NSMakeRect(0, 10, larguraPainel, 26), false);
  for (let i = 0; i < musicas.length; i++) {
    const item = musicas[i];
    const titulo = item.name + (item.folder_name !== item.name ? ' (' + item.folder_name + ')' : '');
    popup.addItemWithTitle(titulo);
  }
  painel.addSubview(popup);

  alert.accessoryView = painel;
  prepararJanelaPrimeiroPlano(alert);

  const resposta = alert.runModal;
  if (resposta !== $.NSAlertFirstButtonReturn) {
    return null;
  }

  const indiceEscolhido = Number(popup.indexOfSelectedItem);
  return musicas[indiceEscolhido];
}

function confirmarAtualizacao(musica) {
  const alert = $.NSAlert.alloc.init;
  alert.messageText = 'Confirmar Atualização';
  alert.informativeText = 'Você tem certeza que deseja atualizar a música:\n\n' +
    '🎵 ' + musica.name + '\n📁 Pasta: ' + musica.folder_name + '\n\n' +
    'Esta ação enviará novamente os áudios e o mapa de arranjo atualizado para o grupo do Telegram.';

  const icone = criarIconeMusica();
  if (icone && icone.isValid) alert.icon = icone;

  alert.addButtonWithTitle('Sim, Atualizar');
  alert.addButtonWithTitle('Cancelar');

  prepararJanelaPrimeiroPlano(alert);
  const resposta = alert.runModal;
  return resposta === $.NSAlertFirstButtonReturn;
}

// Fluxo Principal
let resultado = '';
const musicas = lerEntradaMusicas();
const escolhida = selecionarMusica(musicas);

if (escolhida) {
  const confirmado = confirmarAtualizacao(escolhida);
  if (confirmado) {
    resultado = JSON.stringify({
      folder_id: escolhida.id,
      name: escolhida.name,
      folder_name: escolhida.folder_name,
      confirmado: true
    });
  }
}

resultado;
