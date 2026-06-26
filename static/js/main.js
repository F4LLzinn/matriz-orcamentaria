document.addEventListener('DOMContentLoaded', () => {
    const temaSalvo = localStorage.getItem('tema') || 'light';
    document.documentElement.setAttribute('data-theme', temaSalvo);
    
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.checked = (temaSalvo === 'dark');
        toggle.addEventListener('change', (e) => {
            const novoTema = e.target.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', novoTema);
            localStorage.setItem('tema', novoTema);
        });
    }

    const fileInputOrcamento = document.getElementById('arquivo_input');
    if (fileInputOrcamento) {
        fileInputOrcamento.addEventListener('change', () => {
            if (fileInputOrcamento.files.length > 0) {
                enviarLoteOrcamento(fileInputOrcamento.files);
            }
        });
    }

    const fileInputRegional = document.getElementById('arquivo_regional_input');
    if (fileInputRegional) {
        fileInputRegional.addEventListener('change', () => {
            if (fileInputRegional.files.length > 0) {
                enviarLoteRegional(fileInputRegional.files);
            }
        });
    }
});

window.alternarTema = function() {
    const checkbox = document.getElementById('theme-toggle');
    if (!checkbox) return;
    const novoTema = checkbox.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', novoTema);
    localStorage.setItem('tema', novoTema);
};

function removerPlanilhaLocal(nomeArquivo) {
    const alertBox = document.getElementById('resultado');
    alertBox.style.display = 'none';

    if (!confirm(`Deseja remover permanentemente o arquivo "${nomeArquivo}"?`)) return;

    fetch(`/limpar/orcamento/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        alertBox.className = data.status === 'sucesso' ? 'alert alert-success' : 'alert alert-error';
        alertBox.innerText = data.mensagem;
        alertBox.style.display = 'block';
        if (data.status === 'sucesso') setTimeout(() => { window.location.reload(); }, 1200);
    });
}

function removerPlanilhasEmLote() {
    const checkboxes = document.querySelectorAll('.chk-arquivo-delete:checked');
    const alertBox = document.getElementById('resultado');
    alertBox.style.display = 'none';

    if (checkboxes.length === 0) {
        alert('Selecione pelo menos uma planilha para exclusão.');
        return;
    }

    if (!confirm(`Deseja remover os ${checkboxes.length} arquivos selecionados?`)) return;

    const btnLote = document.getElementById('btn-remover-lote');
    btnLote.disabled = true;
    btnLote.innerText = "Excluindo...";

    const enviosExclusao = Array.from(checkboxes).map(chk => {
        return fetch(`/limpar/orcamento/${encodeURIComponent(chk.value)}`, { method: 'POST' })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(enviosExclusao).then(resultados => {
        const erros = resultados.filter(r => r.status === 'erro');
        if (erros.length === 0) {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = 'Planilhas removidas com sucesso.';
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1200);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Erro ao remover algumas planilhas.';
            alertBox.style.display = 'block';
            btnLote.disabled = false;
            btnLote.innerText = "🗑️ Excluir Selecionados";
        }
    });
}

function enviarLoteOrcamento(arquivos) {
    if (arquivos.length === 0) return;
    const txtLabel = document.getElementById('label_orcamento');
    const alertBox = document.getElementById('resultado');
    alertBox.style.display = 'none';
    txtLabel.innerText = `Enviando ${arquivos.length} arquivo(s)...`;

    const envios = Array.from(arquivos).map(arquivo => {
        const formData = new FormData();
        formData.append('arquivo', arquivo);
        return fetch('/upload/orcamento', { method: 'POST', body: formData })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(envios).then(resultados => {
        const erros = resultados.filter(r => r.status === 'erro');
        if (erros.length === 0) {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = 'Upload concluído.';
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1200);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Erro no upload operacional.';
            alertBox.style.display = 'block';
        }
    }).finally(() => {
        txtLabel.innerHTML = 'Clique ou arraste as planilhas de dados (.csv, .xlsx)';
    });
}

function enviarArquivoIpca(arquivo) {
    if (!arquivo) return;
    const wrapper = document.getElementById('wrapper_ipca');
    const inputField = document.getElementById('input_ipca');
    const txtLabel = document.getElementById('label_ipca');
    const alertBox = document.getElementById('resultado');
    
    alertBox.style.display = 'none';
    txtLabel.innerText = "Carregando série histórica...";

    const formData = new FormData();
    formData.append('arquivo', arquivo);

    fetch('/upload/ipca', { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
            inputField.disabled = true;
            wrapper.style.pointerEvents = 'none';
            wrapper.style.opacity = '0.6';
            txtLabel.innerHTML = '<span style="color: #10b981;">✔ Série histórica protegida</span>';
            document.getElementById('btn_limpar_ipca_container').style.display = 'block';
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
        }
    });
}

function limparArquivoIpca() {
    const wrapper = document.getElementById('wrapper_ipca');
    const inputField = document.getElementById('input_ipca');
    const txtLabel = document.getElementById('label_ipca');
    const alertBox = document.getElementById('resultado');
    const btnLimpar = document.getElementById('btn_limpar_ipca_container');
    alertBox.style.display = 'none';
    
    fetch('/limpar/ipca', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
            inputField.disabled = false;
            inputField.value = '';
            wrapper.style.pointerEvents = 'auto';
            wrapper.style.opacity = '1';
            txtLabel.innerHTML = 'Clique para importar a série <strong>preco12_ipca12</strong>';
            btnLimpar.style.display = 'none';
        }
    });
}

function dispararPipeline() {
    const btn = document.getElementById('btn-run');
    const alertBox = document.getElementById('resultado');
    const anoBase = document.getElementById('ano_base').value;
    const modoExecucao = document.querySelector('input[name="modo_execucao"]:checked').value;

    alertBox.style.display = 'none';
    document.getElementById('bloco-downloads').style.display = 'none';
    btn.disabled = true;
    btn.innerText = "Computando de acordo com as regras de negócio...";

    fetch('/processar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ano_base: anoBase, modo: modoExecucao })
    })
    .then(res => res.json())
    .then(data => {
        alertBox.className = data.status === 'sucesso' ? 'alert alert-success' : 'alert alert-error';
        alertBox.innerText = data.mensagem;
        alertBox.style.display = 'block';
        if (data.status === 'sucesso') document.getElementById('bloco-downloads').style.display = 'block';
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerText = "Executar Processamento de Dados";
    });
}

function enviarLoteRegional(arquivos) {
    if (arquivos.length === 0) return;
    const txtLabel = document.getElementById('label_regional');
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';
    txtLabel.innerText = `Enviando ${arquivos.length} matriz(es)...`;

    const envios = Array.from(arquivos).map(arquivo => {
        const formData = new FormData();
        formData.append('arquivo', arquivo);
        return fetch('/upload/regional', { method: 'POST', body: formData })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(envios).then(resultados => {
        const erros = resultados.filter(r => r.status === 'erro');
        if (erros.length === 0) {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = 'Matrizes territoriais carregadas.';
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1200);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Erro operacional no upload regional.';
            alertBox.style.display = 'block';
        }
    });
}

function removerPlanilhaRegional(nomeArquivo) {
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';

    if (!confirm(`Deseja remover o arquivo "${nomeArquivo}"?`)) return;

    fetch(`/limpar/regional/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        alertBox.className = data.status === 'sucesso' ? 'alert alert-success' : 'alert alert-error';
        alertBox.innerText = data.mensagem;
        alertBox.style.display = 'block';
        if (data.status === 'sucesso') setTimeout(() => { window.location.reload(); }, 1200);
    });
}

function removerPlanilhasRegionalEmLote() {
    const checkboxes = document.querySelectorAll('.chk-regional-delete:checked');
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';

    if (checkboxes.length === 0) {
        alert('Selecione pelo menos uma planilha.');
        return;
    }

    if (!confirm('Deseja remover as planilhas selecionadas?')) return;

    const btnLote = document.getElementById('btn-remover-lote-reg');
    btnLote.disabled = true;

    const enviosExclusao = Array.from(checkboxes).map(chk => {
        return fetch(`/limpar/regional/${encodeURIComponent(chk.value)}`, { method: 'POST' })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(enviosExclusao).then(resultados => {
        alertBox.className = 'alert alert-success';
        alertBox.innerText = 'Operação de limpeza concluída.';
        alertBox.style.display = 'block';
        setTimeout(() => { window.location.reload(); }, 1200);
    });
}

function dispararPipelineRegional() {
    const btn = document.getElementById('btn-run-regional');
    const alertBox = document.getElementById('resultado-regional');
    const indicador = document.querySelector('input[name="indicador_regional"]:checked').value;
    const chkMatrizes = document.getElementById('exportar_matrizes');
    const exportarMatrizes = chkMatrizes ? chkMatrizes.checked : false;

    // 🌟 CAPTURA O FILTRO DO SELECIONADOR GEOGRÁFICO
    const filtroMacro = document.getElementById('filtro_macroregiao');
    const filtroMacroregiao = filtroMacro ? filtroMacro.value : 'Todos';

    if (btn) { btn.disabled = true; btn.innerText = "Executando equações matriciais..."; }
    if (alertBox) alertBox.style.display = 'none';
    document.getElementById('bloco-downloads-regional').style.display = 'none';

    fetch('/processar_regional', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            indicador: indicador,
            exportar_matrizes: exportarMatrizes,
            filtro_macroregiao: filtroMacroregiao // 🌟 Envia dinamicamente a escolha do usuário
        })
    })
    .then(res => res.json())
    .then(data => {
        alertBox.className = data.status === 'sucesso' ? 'alert alert-success' : 'alert alert-error';
        alertBox.innerText = data.mensagem;
        alertBox.style.display = 'block';
        if (data.status === 'sucesso') document.getElementById('bloco-downloads-regional').style.display = 'block';
    })
    .finally(() => {
        if (btn) { btn.disabled = false; btn.innerText = "Processar Dados Regionais"; }
    });
}