/**
 * Front‑end logic for StockPortfolioTracker.
 * Uses modern ES6+ features and fetch API.
 */

const STORAGE_KEY = "portfolio_holdings";

/**
 * Retrieve holdings from localStorage or initialise an empty array.
 * @returns {Array<{symbol:string, shares:number}>}
 */
function loadHoldings() {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
}

/**
 * Persist holdings to localStorage.
 * @param {Array} holdings
 */
function saveHoldings(holdings) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
}

/**
 * Render the portfolio table based on current holdings.
 */
async function renderPortfolio() {
    const holdings = loadHoldings();
    const tbody = document.querySelector("#portfolio-table tbody");
    const totalCell = document.getElementById("total-value");
    tbody.innerHTML = ""; // clear previous rows

    if (holdings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No holdings yet. Add a stock above.</td></tr>`;
        totalCell.textContent = "$0.00";
        return;
    }

    const query = encodeURIComponent(JSON.stringify(holdings));
    try {
        const resp = await fetch(`/api/portfolio?holdings=${query}`);
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Failed to fetch portfolio");
        }
        const data = await resp.json();
        let total = 0;

        data.portfolio.forEach(item => {
            const row = document.createElement("tr");

            const price = item.price !== null ? `$${item.price.toFixed(2)}` : "N/A";
            const value = item.value !== null ? `$${item.value.toFixed(2)}` : "N/A";

            row.innerHTML = `
                <td>${item.symbol}</td>
                <td>${item.shares}</td>
                <td>${price}</td>
                <td>${value}</td>
                <td><button data-symbol="${item.symbol}" class="remove-btn">Remove</button></td>
            `;
            tbody.appendChild(row);

            if (item.value) total += item.value;
        });

        totalCell.textContent = `$${total.toFixed(2)}`;

        // Attach remove handlers
        document.querySelectorAll(".remove-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const sym = btn.dataset.symbol;
                const updated = holdings.filter(h => h.symbol !== sym);
                saveHoldings(updated);
                renderPortfolio();
            });
        });
    } catch (error) {
        console.error("Error rendering portfolio:", error);
        tbody.innerHTML = `<tr><td colspan="5" style="color:red;">${error.message}</td></tr>`;
    }
}

/**
 * Initialise form listeners.
 */
function initForm() {
    const form = document.getElementById("add-stock-form");
    form.addEventListener("submit", event => {
        event.preventDefault();
        const symbolInput = document.getElementById("symbol-input");
        const sharesInput = document.getElementById("shares-input");

        const symbol = symbolInput.value.trim().toUpperCase();
        const shares = parseInt(sharesInput.value, 10);

        if (!symbol || isNaN(shares) || shares <= 0) {
            alert("Please provide a valid ticker and share count.");
            return;
        }

        const holdings = loadHoldings();
        const existing = holdings.find(h => h.symbol === symbol);
        if (existing) {
            existing.shares += shares;
        } else {
            holdings.push({ symbol, shares });
        }
        saveHoldings(holdings);
        form.reset();
        renderPortfolio();
    });
}

/**
 * Auto‑refresh portfolio every 5 minutes.
 */
function startAutoRefresh() {
    setInterval(renderPortfolio, 5 * 60 * 1000);
}

// Entry point
document.addEventListener("DOMContentLoaded", () => {
    initForm();
    renderPortfolio();
    startAutoRefresh();
});