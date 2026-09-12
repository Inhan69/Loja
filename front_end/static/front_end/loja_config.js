(function (global) {
  const STORAGE_KEY = "loja_config_v1";
  const ORIGIN = window.location.origin;

  const CORES_PADRAO = {
    header: "#1f2126",
    sidebar: "#1f2126",
    sidebar2: "#2b2f34",
    destaque: "#5aa2ff",
    acento: "#2b87ff",
    fundo: "#f4f6f9",
    painel: "#ffffff",
    texto: "#1f2937",
  };

  const CORES_CAMPOS = [
    { chave: "header", rotulo: "Barra superior", alvo: "Cabeçalho com a logo" },
    { chave: "sidebar", rotulo: "Menu lateral (topo)", alvo: "Início do degradê" },
    { chave: "sidebar2", rotulo: "Menu lateral (base)", alvo: "Fim do degradê" },
    { chave: "destaque", rotulo: "Destaque do item ativo", alvo: "Borda do menu selecionado" },
    { chave: "acento", rotulo: "Cor de acento", alvo: "Botões e valores em destaque" },
    { chave: "fundo", rotulo: "Fundo das páginas", alvo: "Área de conteúdo" },
    { chave: "painel", rotulo: "Painéis e cards", alvo: "Caixas brancas internas" },
    { chave: "texto", rotulo: "Texto principal", alvo: "Títulos e conteúdo" },
  ];

  const TEMAS = [
    { id: "edecasa", rotulo: "É de casa", cores: CORES_PADRAO },
    {
      id: "oceano",
      rotulo: "Oceano",
      cores: {
        header: "#0f172a", sidebar: "#0b1f3a", sidebar2: "#164e7a",
        destaque: "#38bdf8", acento: "#0284c7", fundo: "#e8f3fb",
        painel: "#ffffff", texto: "#0f172a",
      },
    },
    {
      id: "vinho",
      rotulo: "Vinho",
      cores: {
        header: "#3b0d16", sidebar: "#4a151e", sidebar2: "#6b1d2a",
        destaque: "#fb7185", acento: "#be123c", fundo: "#fdf2f4",
        painel: "#ffffff", texto: "#1f1316",
      },
    },
    {
      id: "floresta",
      rotulo: "Floresta",
      cores: {
        header: "#052e16", sidebar: "#064e3b", sidebar2: "#065f46",
        destaque: "#34d399", acento: "#059669", fundo: "#ecfdf5",
        painel: "#ffffff", texto: "#064e3b",
      },
    },
  ];

  const ATALHOS_PADRAO = {
    dashboard: { code: "Digit1", alt: true, ctrl: false, shift: false },
    produtos: { code: "Digit2", alt: true, ctrl: false, shift: false },
    clientes: { code: "Digit3", alt: true, ctrl: false, shift: false },
    vendas: { code: "Digit4", alt: true, ctrl: false, shift: false },
    configuracoes: { code: "Digit5", alt: true, ctrl: false, shift: false },
    busca: { code: "KeyF", alt: true, ctrl: false, shift: false },
    novo: { code: "KeyN", alt: true, ctrl: false, shift: false },
    finalizar: { code: "Enter", alt: true, ctrl: false, shift: false },
    ajuda: { code: "Slash", alt: true, ctrl: false, shift: false },
  };

  const ATALHOS_META = [
    { chave: "dashboard", rotulo: "Abrir Dashboard", grupo: "Navegação" },
    { chave: "produtos", rotulo: "Abrir Produtos", grupo: "Navegação" },
    { chave: "clientes", rotulo: "Abrir Clientes", grupo: "Navegação" },
    { chave: "vendas", rotulo: "Abrir Vendas", grupo: "Navegação" },
    { chave: "configuracoes", rotulo: "Abrir Configurações", grupo: "Navegação" },
    { chave: "busca", rotulo: "Focar a busca", grupo: "Ações" },
    { chave: "novo", rotulo: "Novo produto / cliente", grupo: "Ações" },
    { chave: "finalizar", rotulo: "Finalizar venda", grupo: "Ações" },
    { chave: "ajuda", rotulo: "Mostrar atalhos", grupo: "Ações" },
  ];

  const NAVEGACAO = ["dashboard", "produtos", "clientes", "vendas", "configuracoes"];
  const BLOQUEADAS = new Set(["Tab", "Escape", "Meta", "Control", "Alt", "Shift"]);

  let capturando = null;
  let capturaHandler = null;
  let capturaRemota = false;

  function clonar(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  function mesclar(base, extra) {
    return Object.assign(clonar(base), extra || {});
  }

  function padrao() {
    return { cores: clonar(CORES_PADRAO), atalhos: clonar(ATALHOS_PADRAO) };
  }

  function carregar() {
    const base = padrao();
    try {
      const bruto = localStorage.getItem(STORAGE_KEY);
      if (!bruto) return base;
      const salvo = JSON.parse(bruto);
      base.cores = mesclar(CORES_PADRAO, salvo.cores);
      base.atalhos = mesclar(ATALHOS_PADRAO, salvo.atalhos);
      return base;
    } catch (err) {
      return base;
    }
  }

  function salvar(config) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    aplicar(config);
    avisar("config-atualizada");
  }

  function aplicarCores(cores) {
    const root = document.documentElement;
    const mapa = {
      "--loja-header": cores.header,
      "--loja-sidebar": cores.sidebar,
      "--loja-sidebar-2": cores.sidebar2,
      "--loja-destaque": cores.destaque,
      "--loja-acento": cores.acento,
      "--loja-fundo": cores.fundo,
      "--loja-painel": cores.painel,
      "--loja-texto": cores.texto,
      "--panel-color": cores.painel,
      "--text-color": cores.texto,
    };
    Object.entries(mapa).forEach(([chave, valor]) => root.style.setProperty(chave, valor));
  }

  function aplicar(config) {
    aplicarCores((config || carregar()).cores);
  }

  function rotuloTecla(code) {
    if (!code) return "?";
    if (code.startsWith("Key")) return code.slice(3);
    if (code.startsWith("Digit")) return code.slice(5);
    if (code.startsWith("Numpad")) return "Num " + code.slice(6);
    const nomes = {
      Slash: "/",
      Enter: "Enter",
      Space: "Espaço",
      Minus: "-",
      Equal: "=",
      Comma: ",",
      Period: ".",
      Semicolon: ";",
      Quote: "'",
      Backquote: "`",
      BracketLeft: "[",
      BracketRight: "]",
      Backslash: "\\",
      ArrowUp: "↑",
      ArrowDown: "↓",
      ArrowLeft: "←",
      ArrowRight: "→",
    };
    return nomes[code] || code;
  }

  function formatarAtalho(atalho) {
    if (!atalho || !atalho.code) return "—";
    const partes = [];
    if (atalho.ctrl) partes.push("Ctrl");
    if (atalho.alt) partes.push("Alt");
    if (atalho.shift) partes.push("Shift");
    partes.push(rotuloTecla(atalho.code));
    return partes.join(" + ");
  }

  function lerEvento(event) {
    return {
      code: event.code,
      alt: event.altKey,
      ctrl: event.ctrlKey,
      shift: event.shiftKey,
    };
  }

  function mesmaCombinacao(a, b) {
    return a && b && a.code === b.code && !!a.alt === !!b.alt && !!a.ctrl === !!b.ctrl && !!a.shift === !!b.shift;
  }

  function combinacaoValida(atalho) {
    if (!atalho || BLOQUEADAS.has(atalho.code)) return false;
    if (/^F\d{1,2}$/.test(atalho.code)) return true;
    return atalho.alt || atalho.ctrl;
  }

  function conflito(atalhos, chaveAtual, candidato) {
    return Object.keys(atalhos).find(
      (chave) => chave !== chaveAtual && mesmaCombinacao(atalhos[chave], candidato)
    );
  }

  function ehShell() {
    return Boolean(global.LOJA_SHELL);
  }

  function avisar(tipo, extra) {
    const payload = Object.assign({ source: "loja", type: tipo }, extra || {});
    if (ehShell()) {
      const iframe = document.querySelector("iframe[name='conteudo']");
      try {
        iframe?.contentWindow?.postMessage(payload, ORIGIN);
      } catch (err) { /* iframe ainda sem documento */ }
      return;
    }
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(payload, ORIGIN);
    }
  }

  function navegarShell(pagina) {
    const url = (global.LOJA_ROTAS || {})[pagina];
    const iframe = document.querySelector("iframe[name='conteudo']");
    if (url && iframe) iframe.src = url;
    document.querySelectorAll(".bt_painel").forEach((botao) => {
      botao.classList.toggle("ativo", botao.dataset.pagina === pagina);
    });
  }

  function focarBusca() {
    const campo = document.querySelector("#search-input, .campo-busca, input[type='search']");
    if (!campo) return false;
    campo.focus();
    if (typeof campo.select === "function") campo.select();
    return true;
  }

  function executarPagina(comando) {
    if (comando === "busca") {
      focarBusca();
      return;
    }
    if (comando === "novo") {
      document.getElementById("btn-novo-produto")?.click();
      document.getElementById("btn-novo-cliente")?.click();
      return;
    }
    if (comando === "finalizar") {
      document.getElementById("btn-finalizar")?.click();
    }
  }

  function montarAjuda() {
    let overlay = document.getElementById("loja-ajuda-atalhos");
    if (overlay) return overlay;
    overlay = document.createElement("div");
    overlay.id = "loja-ajuda-atalhos";
    overlay.innerHTML = `
      <div class="loja-ajuda-caixa">
        <div class="loja-ajuda-topo">
          <strong>Atalhos do teclado</strong>
          <button type="button" id="loja-ajuda-fechar">Fechar</button>
        </div>
        <div class="loja-ajuda-lista"></div>
        <p>Altere as teclas em Configurações.</p>
      </div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) overlay.classList.remove("aberto");
    });
    overlay.querySelector("#loja-ajuda-fechar").addEventListener("click", () => {
      overlay.classList.remove("aberto");
    });
    return overlay;
  }

  function atualizarListaAjuda(overlay) {
    const lista = overlay.querySelector(".loja-ajuda-lista");
    const { atalhos } = carregar();
    lista.innerHTML = ATALHOS_META.map((item) => (
      `<div><span>${item.rotulo}</span><kbd>${formatarAtalho(atalhos[item.chave])}</kbd></div>`
    )).join("");
  }

  function toggleAjuda(abrir) {
    if (!ehShell()) {
      avisar("ajuda");
      return;
    }
    const overlay = montarAjuda();
    atualizarListaAjuda(overlay);
    const deveAbrir = abrir === undefined ? !overlay.classList.contains("aberto") : Boolean(abrir);
    overlay.classList.toggle("aberto", deveAbrir);
  }

  function aoComando(comando) {
    if (comando === "ajuda") {
      toggleAjuda();
      return;
    }
    if (ehShell()) {
      document.getElementById("loja-ajuda-atalhos")?.classList.remove("aberto");
    }
    if (NAVEGACAO.includes(comando)) {
      if (ehShell()) navegarShell(comando);
      else avisar("navegar", { pagina: comando });
      return;
    }
    if (ehShell()) {
      avisar("executar", { comando });
      return;
    }
    executarPagina(comando);
  }

  function onKeydown(event) {
    if (event.isComposing) return;
    if (capturando || capturaRemota) return;

    if (event.code === "Escape") {
      if (ehShell()) {
        const overlay = document.getElementById("loja-ajuda-atalhos");
        if (overlay?.classList.contains("aberto")) {
          overlay.classList.remove("aberto");
          event.preventDefault();
        }
      } else {
        avisar("ajuda-fechar");
      }
      return;
    }

    if (event.repeat) return;
    const candidato = lerEvento(event);
    const { atalhos } = carregar();
    const comando = Object.keys(atalhos).find((chave) => mesmaCombinacao(atalhos[chave], candidato));
    if (!comando) return;
    event.preventDefault();
    event.stopPropagation();
    aoComando(comando);
  }

  function onMessage(event) {
    if (event.origin !== ORIGIN) return;
    const dados = event.data;
    if (!dados || dados.source !== "loja") return;
    if (dados.type === "navegar" && ehShell()) navegarShell(dados.pagina);
    if (dados.type === "ajuda" && ehShell()) toggleAjuda();
    if (dados.type === "ajuda-fechar" && ehShell()) toggleAjuda(false);
    if (dados.type === "executar" && !ehShell()) executarPagina(dados.comando);
    if (dados.type === "config-atualizada") aplicar(carregar());
    if (dados.type === "cores-preview" && dados.cores) aplicarCores(dados.cores);
    if (dados.type === "captura") capturaRemota = Boolean(dados.ativo);
  }

  function iniciar() {
    aplicar(carregar());
    document.addEventListener("keydown", onKeydown, true);
    window.addEventListener("message", onMessage);
    window.addEventListener("storage", (event) => {
      if (event.key === STORAGE_KEY) aplicar(carregar());
    });
    if (ehShell()) {
      const iframe = document.querySelector("iframe[name='conteudo']");
      iframe?.addEventListener("load", () => {
        try {
          iframe.contentWindow.focus();
        } catch (err) { /* ignore */ }
      });
    }
  }

  global.LojaConfig = {
    CORES_PADRAO,
    CORES_CAMPOS,
    TEMAS,
    ATALHOS_PADRAO,
    ATALHOS_META,
    padrao,
    carregar,
    salvar,
    aplicar,
    aplicarCores,
    previewCores(cores) {
      aplicarCores(cores);
      avisar("cores-preview", { cores });
    },
    formatarAtalho,
    lerEvento,
    combinacaoValida,
    conflito,
    iniciarCaptura(chave, aoCapturar) {
      if (capturaHandler) document.removeEventListener("keydown", capturaHandler, true);
      capturando = chave;
      avisar("captura", { ativo: true });
      capturaHandler = (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (event.code === "Escape") {
          capturando = null;
          document.removeEventListener("keydown", capturaHandler, true);
          capturaHandler = null;
          avisar("captura", { ativo: false });
          aoCapturar(null, "cancelado");
          return;
        }
        const candidato = lerEvento(event);
        if (!combinacaoValida(candidato)) {
          aoCapturar(null, "invalido");
          return;
        }
        capturando = null;
        document.removeEventListener("keydown", capturaHandler, true);
        capturaHandler = null;
        avisar("captura", { ativo: false });
        aoCapturar(candidato, "ok");
      };
      document.addEventListener("keydown", capturaHandler, true);
    },
    cancelarCaptura() {
      capturando = null;
      if (capturaHandler) {
        document.removeEventListener("keydown", capturaHandler, true);
        capturaHandler = null;
      }
      avisar("captura", { ativo: false });
    },
    estaCapturando() {
      return Boolean(capturando);
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})(window);
