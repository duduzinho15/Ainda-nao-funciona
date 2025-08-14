// ===== GERENCIAMENTO DE TEMAS =====
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || this.getSystemTheme();
        this.init();
    }

    // Detecta a preferência do sistema operacional
    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Inicializa o tema
    init() {
        this.applyTheme(this.currentTheme);
        this.updateToggleButton();
        this.setupEventListeners();
    }

    // Aplica o tema selecionado
    applyTheme(theme) {
        const body = document.body;
        
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            this.currentTheme = 'dark';
        } else {
            body.classList.remove('dark-mode');
            this.currentTheme = 'light';
        }
        
        localStorage.setItem('theme', this.currentTheme);
        this.updateToggleButton();
    }

    // Alterna entre os temas
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        // Adiciona animação de transição
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    // Atualiza o botão de toggle
    updateToggleButton() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('i');
            const text = toggleBtn.querySelector('span');
            
            if (this.currentTheme === 'dark') {
                icon.className = 'fas fa-sun';
                text.textContent = 'Modo Claro';
            } else {
                icon.className = 'fas fa-moon';
                text.textContent = 'Modo Escuro';
            }
        }
    }

    // Configura os event listeners
    setupEventListeners() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Escuta mudanças na preferência do sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// ===== GERENCIAMENTO DE DADOS =====
class DataManager {
    constructor() {
        this.init();
    }

    init() {
        this.updateLastUpdate();
        this.setupAutoRefresh();
        this.addTableInteractions();
    }

    // Atualiza a última atualização
    updateLastUpdate() {
        const now = new Date();
        const options = {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        const formattedDate = now.toLocaleDateString('pt-BR', options);
        const lastUpdateElement = document.querySelector('.last-update');
        const lastUpdateSummary = document.querySelector('.last-update-summary');
        const dataHojeElement = document.getElementById('data-hoje');
        
        if (lastUpdateElement) {
            lastUpdateElement.textContent = `Última Atualização: ${formattedDate}`;
        }
        
        if (lastUpdateSummary) {
            lastUpdateSummary.textContent = formattedDate;
        }
        
        if (dataHojeElement) {
            dataHojeElement.textContent = now.toLocaleDateString('pt-BR');
        }
    }

    // Configura atualização automática
    setupAutoRefresh() {
        // Atualiza a cada 30 segundos
        setInterval(() => {
            this.updateLastUpdate();
        }, 30000);
    }

    // Adiciona interações na tabela
    addTableInteractions() {
        const tableRows = document.querySelectorAll('.table tbody tr');
        
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.transition = 'all 0.2s ease';
            });
            
            // Adiciona efeito de clique para expandir detalhes
            row.addEventListener('click', (e) => {
                // Não expande se clicar em links ou botões
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                    return;
                }
                
                this.toggleRowDetails(row);
            });
        });
    }

    // Expande/recolhe detalhes da linha
    toggleRowDetails(row) {
        const detailsRow = row.nextElementSibling;
        
        if (detailsRow && detailsRow.classList.contains('details-row')) {
            // Remove linha de detalhes existente
            detailsRow.remove();
        } else {
            // Adiciona linha de detalhes
            this.addDetailsRow(row);
        }
    }

    // Adiciona linha de detalhes
    addDetailsRow(row) {
        const detailsRow = document.createElement('tr');
        detailsRow.className = 'details-row';
        detailsRow.style.backgroundColor = 'var(--bg-secondary)';
        
        const detailsCell = document.createElement('td');
        detailsCell.colSpan = 7; // Ajuste conforme o número de colunas
        detailsCell.style.padding = '1rem';
        
        // Obtém dados da linha original
        const cells = row.querySelectorAll('td');
        const titulo = cells[2]?.textContent || 'N/A';
        const preco = cells[3]?.textContent || 'N/A';
        const loja = cells[1]?.textContent || 'N/A';
        
        detailsCell.innerHTML = `
            <div class="details-content">
                <h4 style="margin-bottom: 0.5rem; color: var(--accent-color);">${titulo}</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <strong>Loja:</strong> ${loja}<br>
                        <strong>Preço:</strong> ${preco}
                    </div>
                    <div>
                        <strong>Data de Postagem:</strong> ${cells[0]?.textContent || 'N/A'}<br>
                        <strong>Fonte:</strong> ${cells[5]?.textContent || 'N/A'}
                    </div>
                </div>
            </div>
        `;
        
        detailsRow.appendChild(detailsCell);
        row.parentNode.insertBefore(detailsRow, row.nextSibling);
    }
}

// ===== UTILITÁRIOS =====
class Utils {
    // Formata números para exibição
    static formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // Adiciona animação de entrada
    static animateIn(element, delay = 0) {
        setTimeout(() => {
            element.classList.add('fade-in');
        }, delay);
    }

    // Copia texto para clipboard
    static copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copiado para clipboard!');
        }).catch(() => {
            this.showToast('Erro ao copiar');
        });
    }

    // Mostra toast de notificação
    static showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-color);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: var(--shadow);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Anima entrada
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove após 3 segundos
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', () => {
    // Inicializa o gerenciador de temas
    const themeManager = new ThemeManager();
    
    // Inicializa o gerenciador de dados
    const dataManager = new DataManager();
    
    // Adiciona animações de entrada
    const elements = document.querySelectorAll('.stat-card, .table-container');
    elements.forEach((element, index) => {
        Utils.animateIn(element, index * 100);
    });
    
    // Adiciona funcionalidade de busca (opcional)
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
    
    // Adiciona funcionalidade de ordenação (opcional)
    const sortableHeaders = document.querySelectorAll('.table th[data-sortable]');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            const currentOrder = header.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Remove indicadores de ordenação anteriores
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                delete h.dataset.order;
            });
            
            // Adiciona indicador de ordenação atual
            header.classList.add(`sort-${newOrder}`);
            header.dataset.order = newOrder;
            
            // Aqui você implementaria a lógica de ordenação
            console.log(`Ordenando por ${column} em ordem ${newOrder}`);
        });
    });
    
    console.log('Dashboard inicializado com sucesso! 🚀');
});

// ===== FUNÇÕES GLOBAIS =====
window.DashboardUtils = Utils;
window.ThemeManager = ThemeManager;
