// Seletor Nativo de Pasta Local para Upload (macOS, JavaScript for Automation).
//
// Execução:   osascript -l JavaScript scripts/seletor_pasta_upload.js
// Saída:      Caminho da pasta selecionada se confirmado; texto vazio se cancelado.

ObjC.import('Cocoa');

const app = $.NSApplication.sharedApplication;
app.setActivationPolicy($.NSApplicationActivationPolicyRegular);

function selecionarPastaLocal() {
  const panel = $.NSOpenPanel.openPanel;
  panel.canChooseFiles = false;
  panel.canChooseDirectories = true;
  panel.allowsMultipleSelection = false;
  panel.canCreateDirectories = false;
  panel.title = 'Upload de Música para OneDrive';
  panel.message = 'Selecione a pasta da música que deseja enviar para o OneDrive:';
  panel.prompt = 'Enviar Pasta';

  // Abre posicionado por padrão no diretório de projetos da igreja
  const caminhoPadrao = '/Users/marques/Documents/01 PROJECTS/40-49 Igreja/40.01 - Sets Ministério de Louvor';
  panel.directoryURL = $.NSURL.fileURLWithPath(caminhoPadrao);

  // Força o seletor a ficar no topo absoluto
  panel.level = $.NSScreenSaverWindowLevel;
  panel.hidesOnDeactivate = false;
  panel.orderFrontRegardless;

  $.NSTimer.scheduledTimerWithTimeIntervalRepeatsBlock(0.05, false, function () {
    try {
      panel.level = $.NSScreenSaverWindowLevel;
      panel.orderFrontRegardless;
      app.activateIgnoringOtherApps(true);
    } catch (err) {}
  });

  app.activateIgnoringOtherApps(true);

  const resposta = panel.runModal;
  if (resposta === $.NSModalResponseOK) {
    const url = panel.URLs.objectAtIndex(0);
    return ObjC.unwrap(url.path);
  }
  return '';
}

selecionarPastaLocal();
