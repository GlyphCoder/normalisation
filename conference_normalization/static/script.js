document.addEventListener('DOMContentLoaded', function() {
    const fdsContainer = document.getElementById('fds-container');
    const addFdBtn = document.getElementById('add-fd');
    const normalizeBtn = document.getElementById('normalize-btn');
    const resultsDiv = document.getElementById('results');
    
    // Add FD row
    addFdBtn.addEventListener('click', function() {
        const fdRow = document.createElement('div');
        fdRow.className = 'fd-row animate__animated animate__fadeIn';
        fdRow.innerHTML = `
            <input type="text" class="fd-left" placeholder="left side">
            <span>→</span>
            <input type="text" class="fd-right" placeholder="right side">
            <button class="remove-fd">×</button>
        `;
        fdsContainer.appendChild(fdRow);
        
        // Add remove functionality with animation
        fdRow.querySelector('.remove-fd').addEventListener('click', function() {
            fdRow.classList.add('animate__animated', 'animate__fadeOut');
            setTimeout(() => fdRow.remove(), 500);
        });
    });
    
    // Normalize button
    normalizeBtn.addEventListener('click', function() {
        // Add loading animation
        normalizeBtn.innerHTML = '<span class="animate__animated animate__fadeIn">Processing...</span>';
        normalizeBtn.disabled = true;
        normalizeBtn.classList.remove('animate__pulse');
        
        // Get attributes as array
        const attributes = document.getElementById('attributes').value
            .split(',')
            .map(attr => attr.trim())
            .filter(attr => attr);
        
        // Get FDs with arrays for left and right
        const fds = Array.from(document.querySelectorAll('.fd-row')).map(row => {
            return {
                left: row.querySelector('.fd-left').value.split(',').map(s => s.trim()).filter(s => s),
                right: row.querySelector('.fd-right').value.split(',').map(s => s.trim()).filter(s => s)
            };
        }).filter(fd => fd.left.length > 0 && fd.right.length > 0);
        
        fetch('/normalize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                attributes: attributes,
                fds: fds
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || 'Server error') });
            }
            return response.json();
        })
        .then(data => {
            showResults(data);
            normalizeBtn.innerHTML = 'Normalize Schema';
            normalizeBtn.disabled = false;
            normalizeBtn.classList.add('animate__pulse');
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message);
            normalizeBtn.innerHTML = 'Try Again';
            setTimeout(() => {
                normalizeBtn.innerHTML = 'Normalize Schema';
                normalizeBtn.disabled = false;
                normalizeBtn.classList.add('animate__pulse');
            }, 2000);
        });
    });
    
    function showResults(data) {
        resultsDiv.innerHTML = '';
        
        for (const [step, stepData] of Object.entries(data)) {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'normalization-step animate__animated animate__fadeInUp';
            
            stepDiv.innerHTML = `
                <h3>${step}</h3>
                <p>${stepData.description}</p>
            `;
            
            stepData.tables.forEach(table => {
                const tableDiv = document.createElement('div');
                tableDiv.className = 'table-container';
                
                // Create table element
                const tableEl = document.createElement('table');
                tableEl.className = 'schema-table';
                
                // Create table header
                const thead = document.createElement('thead');
                thead.innerHTML = `
                    <tr>
                        <th colspan="2">${table.name}</th>
                    </tr>
                    <tr>
                        <th>Attribute</th>
                        <th>Type</th>
                    </tr>
                `;
                
                // Create table body
                const tbody = document.createElement('tbody');
                table.attributes.forEach(attr => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${attr}</td>
                        <td>${inferType(attr)}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                tableEl.appendChild(thead);
                tableEl.appendChild(tbody);
                tableDiv.appendChild(tableEl);
                stepDiv.appendChild(tableDiv);
            });
            
            resultsDiv.appendChild(stepDiv);
        }
    }
    
    function showError(message) {
        resultsDiv.innerHTML = `
            <div class="error-message animate__animated animate__shakeX">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }
    
    // Helper function to infer attribute types
    function inferType(attr) {
        if (attr.includes('_id')) return 'VARCHAR(50) PRIMARY KEY';
        if (attr.includes('date')) return 'DATE';
        if (attr.includes('name') || attr.includes('title')) return 'VARCHAR(100)';
        if (attr.includes('email')) return 'VARCHAR(100)';
        if (attr.includes('comments') || attr.includes('abstract')) return 'TEXT';
        if (attr.includes('decision')) return 'ENUM("accept","reject")';
        if (attr.includes('path')) return 'VARCHAR(255)';
        return 'VARCHAR(255)';
    }
});