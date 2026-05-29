document.addEventListener('DOMContentLoaded', () => {
    // --- GERENCIAMENTO SEGURO E PRECOCE DE TEMA ---
    const temaSalvo = localStorage.getItem('tema') || 'light';
    document.documentElement.setAttribute('data-theme', temaSalvo);
    
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.checked = (temaSalvo === 'dark');
        
        // Ouvinte moderno direto no elemento (mata o problema de escopo do HTML)
        toggle.addEventListener('change', (e) => {
            const novoTema = e.target.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', novoTema);
            localStorage.setItem('tema', novoTema);
        });
    }

    // --- ESCUTAS DO MÓDULO: ORÇAMENTO ---
    const fileInputOrcamento = document.getElementById('arquivo_input');
    if (fileInputOrcamento) {
        fileInputOrcamento.addEventListener('change', () => {
            if (fileInputOrcamento.files.length > 0) {
                enviarLoteOrcamento(fileInputOrcamento.files);
            }
        });
    }

    // --- ESCUTAS DO MÓDULO: ECONOMIA REGIONAL ---
    const fileInputRegional = document.getElementById('arquivo_regional_input');
    if (fileInputRegional) {
        fileInputRegional.addEventListener('change', () => {
            if (fileInputRegional.files.length > 0) {
                enviarLoteRegional(fileInputRegional.files);
            }
        });
    }
});

// Garante compatibilidade caso o HTML chame a função antiga antes do script carregar todo
window.alternarTema = function() {
    const checkbox = document.getElementById('theme-toggle');
    if (!checkbox) return;
    const novoTema = checkbox.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', novoTema);
    localStorage.setItem('tema', novoTema);
};

// ==============================================================================
// 📊 SCRIPT DE CONTROLE: MÓDULO ORÇAMENTÁRIO (SIGA BRASIL)
// ==============================================================================

function removerPlanilhaLocal(nomeArquivo) {
    const alertBox = document.getElementById('resultado');
    alertBox.style.display = 'none';

    if (!confirm(`Deseja remover permanentemente o arquivo "${nomeArquivo}" do seu repositório de dados?`)) {
        return;
    }

    fetch(`/limpar/orcamento/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1200);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
        }
    })
    .catch(() => {
        alertBox.className = 'alert alert-error';
        alertBox.innerText = 'Erro ao processar a solicitação de exclusão do arquivo.';
        alertBox.style.display = 'block';
    });
}

function removerPlanilhasEmLote() {
    const checkboxes = document.querySelectorAll('.chk-arquivo-delete:checked');
    const alertBox = document.getElementById('resultado');
    alertBox.style.display = 'none';

    if (checkboxes.length === 0) {
        alert('Por favor, selecione pelo menos uma planilha para exclusão.');
        return;
    }

    if (!confirm(`Deseja remover permanentemente os ${checkboxes.length} arquivos selecionados do seu repositório de dados?`)) {
        return;
    }

    const btnLote = document.getElementById('btn-remover-lote');
    btnLote.disabled = true;
    btnLote.innerText = "Excluindo...";

    const enviosExclusao = Array.from(checkboxes).map(chk => {
        const nomeArquivo = chk.value;
        return fetch(`/limpar/orcamento/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(enviosExclusao).then(resultados => {
        const erros = resultados.filter(r => r.status === 'erro');
        if (erros.length === 0) {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = `${checkboxes.length} planilha(s) removida(s) com sucesso em lote.`;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Ocorreu um erro ao tentar remover algumas das planilhas selecionadas.';
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
    txtLabel.innerText = `Processando upload de ${arquivos.length} arquivo(s)...`;

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
            alertBox.innerText = `${arquivos.length} planilha(s) carregada(s) com sucesso.`;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Falha no processamento das planilhas. Verifique o formato dos arquivos.';
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
    txtLabel.innerText = "Carregando série histórica de preços...";

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
            txtLabel.innerHTML = '<span style="color: #10b981;">✔ Série histórica carregada e protegida</span>';
            document.getElementById('btn_limpar_ipca_container').style.display = 'block';
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
            txtLabel.innerHTML = 'Clique para importar a série <strong>preco12_ipca12</strong>';
        }
    })
    .catch(() => {
        alertBox.className = 'alert alert-error';
        alertBox.innerText = 'Erro na transmissão da série IPCA. Tente novamente.';
        alertBox.style.display = 'block';
        txtLabel.innerHTML = 'Clique para importar a série <strong>preco12_ipca12</strong>';
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
    btn.innerText = "Executando processamento...";

    fetch('/processar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ano_base: anoBase, modo: modoExecucao })
    })
    .then(res => {
        return res.json().then(data => {
            if (!res.ok) throw new Error(data.mensagem || 'Erro na execução interna.');
            return data;
        });
    })
    .then(data => {
        alertBox.className = 'alert alert-success';
        alertBox.innerText = data.mensagem;
        alertBox.style.display = 'block';
        document.getElementById('bloco-downloads').style.display = 'block';
    })
    .catch(err => {
        alertBox.className = 'alert alert-error';
        alertBox.innerText = err.message;
        alertBox.style.display = 'block';
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerText = "Executar Processamento de Dados";
    });
}

// ==============================================================================
// 🌍 SCRIPT DE CONTROLE: MÓDULO ECONOMIA REGIONAL
// ==============================================================================

function enviarLoteRegional(arquivos) {
    if (arquivos.length === 0) return;
    const txtLabel = document.getElementById('label_regional');
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';
    txtLabel.innerText = `Processando upload de ${arquivos.length} arquivo(s)...`;

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
            alertBox.innerText = `${arquivos.length} matriz(es) territorial(is) carregada(s) com sucesso.`;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Falha no processamento das planilhas regionais.';
            alertBox.style.display = 'block';
        }
    }).finally(() => {
        txtLabel.innerHTML = 'Clique ou arraste as matrizes de emprego regional<br><small style="color: var(--text-secondary); display: block; margin-top: 4px; font-size: 11px;">Formatos aceitos: .csv, .xlsx</small>';
    });
}

function removerPlanilhaRegional(nomeArquivo) {
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';

    if (!confirm(`Deseja remover permanentemente o arquivo "${nomeArquivo}" do repositório regional?`)) {
        return;
    }

    fetch(`/limpar/regional/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1200);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
        }
    })
    .catch(() => {
        alertBox.className = 'alert alert-error';
        alertBox.innerText = 'Erro ao processar a exclusão do arquivo regional.';
        alertBox.style.display = 'block';
    });
}

function removerPlanilhasRegionalEmLote() {
    const checkboxes = document.querySelectorAll('.chk-regional-delete:checked');
    const alertBox = document.getElementById('resultado-regional');
    alertBox.style.display = 'none';

    if (checkboxes.length === 0) {
        alert('Por favor, selecione pelo menos uma planilha regional para exclusão.');
        return;
    }

    if (!confirm(`Deseja remover permanentemente os ${checkboxes.length} arquivos selecionados?`)) {
        return;
    }

    const btnLote = document.getElementById('btn-remover-lote-reg');
    btnLote.disabled = true;
    btnLote.innerText = "Excluindo...";

    const enviosExclusao = Array.from(checkboxes).map(chk => {
        const nomeArquivo = chk.value;
        return fetch(`/limpar/regional/${encodeURIComponent(nomeArquivo)}`, { method: 'POST' })
            .then(res => res.json())
            .catch(() => ({ status: 'erro' }));
    });

    Promise.all(enviosExclusao).then(resultados => {
        const erros = resultados.filter(r => r.status === 'erro');
        if (erros.length === 0) {
            alertBox.className = 'alert alert-success';
            alertBox.innerText = `${checkboxes.length} planilha(s) removida(s) com sucesso.`;
            alertBox.style.display = 'block';
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertBox.className = 'alert alert-error';
            alertBox.innerText = 'Erro ao tentar remover algumas planilhas regionais.';
            alertBox.style.display = 'block';
            btnLote.disabled = false;
            btnLote.innerText = "🗑️ Excluir Selecionados";
        }
    });
}

function dispararPipelineRegional() {
    const btn = document.getElementById('btn-run-regional');
    const alertBox = document.getElementById('resultado-regional');
    const indicador = document.querySelector('input[name="indicador_regional"]:checked').value;
    
    // 🌟 Captura o estado da checkbox intermediária
    const chkMatrizes = document.getElementById('exportar_matrizes');
    const exportarMatrizes = chkMatrizes ? chkMatrizes.checked : false;

    if (btn) { btn.disabled = true; btn.innerText = "Calculando..."; }
    if (alertBox) alertBox.style.display = 'none';
    document.getElementById('bloco-downloads-regional').style.display = 'none';

    fetch('/processar_regional', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            indicador: indicador,
            exportar_matrizes: exportarMatrizes // Sent to backend
        })
    })
    .then(res => res.json())
    .then(data => {
        if (alertBox) {
            alertBox.className = data.status === 'sucesso' ? 'alert alert-success' : 'alert alert-error';
            alertBox.innerText = data.mensagem;
            alertBox.style.display = 'block';
        }
        if (data.status === 'sucesso') document.getElementById('bloco-downloads-regional').style.display = 'block';
    })
    .finally(() => {
        if (btn) { btn.disabled = false; btn.innerText = "Processar Dados Regionais"; }
    });
}
// --- UTILITÁRIOS GLOBAIS ---
function abrirDiretorioResultados() {
    fetch('/abrir_pasta', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if (data.status !== 'sucesso') alert(data.mensagem);
    })
    .catch(() => {
        alert('Erro ao requisitar a abertura do diretório local.');
    });
}