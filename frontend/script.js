document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const problemInput = document.getElementById('problem-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const clearBtn = document.getElementById('clear-btn');
    const loadingSection = document.getElementById('loading-section');
    const professorResultsSection = document.getElementById('professor-results');
    const teamResultsSection = document.getElementById('team-results');
    const individualResultsSection = document.getElementById('individual-results');
    const filterSortBar = document.getElementById('filter-sort-bar');
    const tabNavigation = document.getElementById('tab-navigation');
    const teamTab = document.getElementById('team-tab');
    const individualTab = document.getElementById('individual-tab');
    const sortBySelect = document.getElementById('sort-by');
    const filterDepartmentSelect = document.getElementById('filter-department');

    // API URL
    const API_URL = 'http://localhost:5050/api';
    
    let currentResults = [];
    let currentApiData = null;
    let currentMode = 'team'; // 'team' or 'individual'
    
    // --- Event Listeners ---
    analyzeBtn.addEventListener('click', handleAnalyzeClick);
    clearBtn.addEventListener('click', handleClearClick);
    problemInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleAnalyzeClick();
        }
    });
    sortBySelect.addEventListener('change', renderResults);
    filterDepartmentSelect.addEventListener('change', renderResults);
    
    // Tab event listeners
    teamTab.addEventListener('click', () => switchTab('team'));
    individualTab.addEventListener('click', () => switchTab('individual'));

    /**
     * Switch between Team and Individual tabs
     */
    function switchTab(mode) {
        currentMode = mode;
        
        // Update tab appearance
        if (mode === 'team') {
            teamTab.classList.add('text-purple-600', 'border-purple-600', 'bg-purple-50');
            teamTab.classList.remove('text-gray-600', 'border-transparent');
            individualTab.classList.remove('text-purple-600', 'border-purple-600', 'bg-purple-50');
            individualTab.classList.add('text-gray-600', 'border-transparent');
            
            // Show team results, hide individual
            teamResultsSection.classList.remove('hidden');
            individualResultsSection.classList.add('hidden');
        } else {
            individualTab.classList.add('text-purple-600', 'border-purple-600', 'bg-purple-50');
            individualTab.classList.remove('text-gray-600', 'border-transparent');
            teamTab.classList.remove('text-purple-600', 'border-purple-600', 'bg-purple-50');
            teamTab.classList.add('text-gray-600', 'border-transparent');
            
            // Show individual results, hide team
            teamResultsSection.classList.add('hidden');
            individualResultsSection.classList.remove('hidden');
            
            // Render individual results if we have data
            if (currentApiData && currentApiData.individual) {
                renderIndividualResults(currentApiData.individual);
            }
        }
    }

    /**
     * Handle click on the "Analyze Problem" button
     */
    function handleAnalyzeClick() {
        const problemStatement = problemInput.value.trim();
        
        // Validate input
        if (!problemStatement) {
            alert('Please enter a problem statement.');
            return;
        }
        
        teamResultsSection.innerHTML = '<div class="bg-white p-8 rounded-lg shadow-md text-center col-span-full"><p class="text-purple-600 text-lg"><i class="fas fa-spinner fa-spin mr-2"></i>Analyzing problem statement...</p></div>';
        
        // Call API
        analyzeProblem(problemStatement);
    }

    /**
     * Handle click on the "Clear" button
     */
    function handleClearClick() {
        problemInput.value = '';
        problemInput.focus();
        teamResultsSection.innerHTML = '<div class="bg-white p-8 rounded-lg shadow-md text-center col-span-full"><p class="text-gray-600 text-lg">Enter your problem statement above to find professors...</p></div>';
        individualResultsSection.innerHTML = '';
        individualResultsSection.classList.add('hidden');
        teamResultsSection.classList.remove('hidden');
        document.querySelectorAll('.explanation-card').forEach(card => card.remove());
        const tagTableContainer = document.getElementById('tagwise-table-container');
        if (tagTableContainer) tagTableContainer.classList.add('hidden');
        filterSortBar.classList.add('hidden');
        tabNavigation.classList.add('hidden');
        currentResults = [];
        currentApiData = null;
        currentMode = 'team';
        
        // Reset tab appearance
        teamTab.classList.add('text-purple-600', 'border-purple-600', 'bg-purple-50');
        teamTab.classList.remove('text-gray-600', 'border-transparent');
        individualTab.classList.remove('text-purple-600', 'border-purple-600', 'bg-purple-50');
        individualTab.classList.add('text-gray-600', 'border-transparent');
    }

    /**
     * Send problem statement to API and process results
     * @param {string} problemStatement 
     */
    async function analyzeProblem(problemStatement) {
        try {
            const response = await fetch(`${API_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    problem_statement: problemStatement
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Unknown error occurred');
            }
            
            console.log('API Response:', data);
            
            // Store API data for tab switching
            currentApiData = data;
            
            // Process and display results
            currentResults = data.team || [];
            window._allProfsByTag = data.all_profs_by_tag || {};
            
            populateDepartmentFilter(currentResults);
            sortResults(currentResults, sortBySelect.value);
            
            // Show tabs and filter bar
            tabNavigation.classList.remove('hidden');
            filterSortBar.classList.remove('hidden');
            
            // Render the results
            renderResults(data, 'problem');
            
            // Scroll to results
            professorResultsSection.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('Error:', error);
            teamResultsSection.innerHTML = `<div class="bg-white p-8 rounded-lg shadow-md text-center col-span-full"><p class="text-red-600 text-lg">An error occurred: ${error.message}</p></div>`;
        }
    }

    /**
     * Helper functions for sorting and filtering
     */
    function populateDepartmentFilter(results) {
        const departments = [...new Set(results.map(prof => prof.department))];
        filterDepartmentSelect.innerHTML = '<option value="">All Departments</option>';
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            filterDepartmentSelect.appendChild(option);
        });
    }
    
    function sortResults(results, criteria) {
        if (criteria === 'alphabetical') {
            results.sort((a, b) => a.name.localeCompare(b.name));
        } else if (criteria === 'relevance') {
            results.sort((a, b) => b.score - a.score);
        }
    }
    
    function filterResults(results, department) {
        if (!department) return results;
        return results.filter(prof => prof.department === department);
    }
    
    /**
     * Main function to render results 
     */
    function renderResults(apiData, mode) {
        // Clear previous explanation cards
        document.querySelectorAll('.explanation-card').forEach(card => card.remove());
        
        // Create explanation card if we have data
        if (apiData.explanation || (apiData.tags && apiData.tags.length) || (apiData.expertise_tags && Object.keys(apiData.expertise_tags).length)) {
            let expertiseTagsHtml = '';
            if (apiData.expertise_tags && Object.keys(apiData.expertise_tags).length) {
                expertiseTagsHtml = `<div class="expertise-tags mb-3">
                    <b>Expertise Areas:</b>
                    ${Object.entries(apiData.expertise_tags).map(([field, tags]) => 
                        `<div class="expertise-field mb-2">
                            <span class="field-name font-semibold text-purple-800">${field}:</span>
                            <div class="field-tags ml-2">
                                ${tags.map(tag => `<span class='tag keytag text-sm'>${tag}</span>`).join(' ')}
                            </div>
                        </div>`
                    ).join('')}
                </div>`;
            }
            
            const explanationHtml = `
            <div class="explanation-card bg-white rounded-lg shadow-md p-4 mb-6">
                <div class="explanation-title font-bold text-lg mb-2 text-purple-700">Analysis Results</div>
                <div class="explanation-body mb-2">${apiData.explanation ? apiData.explanation : ''}</div>
                ${expertiseTagsHtml}
                ${apiData.tags && apiData.tags.length && !expertiseTagsHtml ? `<div class="key-tags mb-2"><b>Key Tags:</b> ${apiData.tags.map(t => `<span class='tag keytag'>${t}</span>`).join(' ')}</div>` : ''}
                ${apiData.key_domain && Object.keys(apiData.key_domain).length ? `<div class="key-domains mb-2"><b>Key Domains:</b> ${Object.entries(apiData.key_domain).map(([k,v]) => `<span class='tag keytag'>${k}: ${v}</span>`).join(' ')}</div>` : ''}
                ${apiData.grouping_message ? `<div class="grouping-message text-sm text-blue-700 mt-2">${apiData.grouping_message}</div>` : ''}
            </div>`;
            
            filterSortBar.insertAdjacentHTML('beforebegin', explanationHtml);
        }
        
        // Handle team display for problem mode
        if (mode === 'problem' && apiData.team) {
            let profOrder = [];
            let profMap = {};
            apiData.team.forEach(teamProf => {
                if (!profMap[teamProf.name]) {
                    profMap[teamProf.name] = { ...teamProf, tags: [...(teamProf.tags || [])] };
                    profOrder.push(teamProf.name);
                } else {
                    profMap[teamProf.name].tags.push(...(teamProf.tags || []));
                }
            });
            
            function getProfsForTags(tags) {
                const profCount = {};
                tags.forEach(tag => {
                    const allProfs = (apiData.all_profs_by_tag && apiData.all_profs_by_tag[tag]) || [];
                    allProfs.forEach(p => {
                        profCount[p.name] = (profCount[p.name] || 0) + 1;
                    });
                });
                return Object.entries(profCount)
                    .sort((a, b) => b[1] - a[1])
                    .map(([name, count]) => ({ name, count }));
            }
            
            function renderTeamCards() {
                teamResultsSection.innerHTML = '';
                const teamNames = profOrder.filter(name => profMap[name]).join(', ');
                if (teamNames.length > 0) {
                    const summaryBox = `<div id="team-summary-bar" class="bg-purple-100 border border-purple-300 rounded-lg p-4 mb-2 text-center text-lg font-semibold text-purple-900 shadow-md col-span-full w-full" style="grid-column: 1 / -1;">${teamNames} would most probably be able to solve this problem together.<span class="block text-xs text-gray-500 mt-1">(Use dropdowns to swap expertise between professors.)</span></div>`;
                    teamResultsSection.innerHTML += summaryBox;
                }
                if (apiData.not_found_tags && apiData.not_found_tags.length > 0) {
                    teamResultsSection.innerHTML += `<div class="bg-red-100 text-red-700 rounded-lg p-4 col-span-full mb-4">No professor found for: <b>${apiData.not_found_tags.join(', ')}</b></div>`;
                }
                
                profOrder.forEach(profName => {
                    const teamProf = profMap[profName];
                    if (!teamProf) return;
                    const tags = teamProf.tags || [];
                    let profsForDropdown = {};
                    tags.forEach(tag => {
                        const allProfs = (apiData.all_profs_by_tag && apiData.all_profs_by_tag[tag]) || [];
                        allProfs.forEach(p => {
                            if (p.name !== teamProf.name) {
                                profsForDropdown[p.name] = (profsForDropdown[p.name] || 0) + 1;
                            }
                        });
                    });
                    const profsSorted = Object.entries(profsForDropdown)
                        .sort((a, b) => b[1] - a[1])
                        .map(([name, count]) => ({ name, count }));
                    let dropdownHtml = '';
                    if (tags.length === 1) {
                        const tag = tags[0];
                        dropdownHtml = `<div class="mb-4 flex flex-col md:flex-row md:items-center gap-2 w-full justify-between"><span class="flex-1 flex justify-end"><select class="ml-2 border border-gray-300 rounded px-2 py-1 text-sm alt-prof-select w-full max-w-xs" data-tag="${tag}" data-current-prof="${teamProf.name}" data-tags='${JSON.stringify(tags)}'><option value="">Show more options...</option>${profsSorted.map(p => `<option value='${p.name}'>${p.name}</option>`).join('')}</select></span></div>`;
                    } else if (tags.length > 1) {
                        dropdownHtml = `<div class="mb-4 flex flex-col md:flex-row md:items-center gap-2 w-full justify-between"><span class="flex-1 flex justify-end"><select class="ml-2 border border-gray-300 rounded px-2 py-1 text-sm alt-prof-select w-full max-w-xs" data-tag="" data-current-prof="${teamProf.name}" data-tags='${JSON.stringify(tags)}'><option value="">Show more options...</option>${profsSorted.map(p => `<option value='${p.name}'>${p.name} (${p.count} tags in common)</option>`).join('')}</select></span></div>`;
                    }
                    teamResultsSection.innerHTML += `
    <div class="professor-card mb-6" data-prof="${teamProf.name}">
        <div class="p-6 flex-grow">
            <div class="mb-4 flex flex-wrap items-center gap-2">
                ${tags.map(tag => `<span class="tag keytag mr-2 mb-1">${tag}</span>`).join('')}
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2 selectable-prof cursor-pointer" data-prof="${teamProf.name}">${teamProf.name}</h3>
            <p class="text-purple-700 mb-2">${teamProf.department}</p>
            <p class="text-gray-600 mb-2">${teamProf.position || ''}</p>
            <div class="flex gap-4 mb-2">
                <a href="${teamProf.base_url || '#'}" target="_blank" class="text-purple-700 hover:underline text-sm font-medium">Profile</a>
                ${teamProf.google_scholar_url ? `<a href="${teamProf.google_scholar_url}" target="_blank" class="text-blue-700 hover:underline text-sm font-medium">Google Scholar</a>` : ''}
            </div>
        </div>
        <div class="prof-card-footer" style="background: #f3f4f6; border-top: 1px solid #e5e7eb; padding: 1rem 1.2rem;">${dropdownHtml}</div>
    </div>
`;
                });
                
                if (apiData.all_profs_by_tag && Object.keys(apiData.all_profs_by_tag).length > 0) {
                    setTimeout(() => {
                        let tagTableHtml = `<h2 class="text-xl font-bold mb-4 text-purple-800">Tag-wise Professor Availability</h2><div class="overflow-x-auto"><table class="min-w-full bg-white rounded-lg shadow-md"><thead><tr><th class="px-4 py-2 border-b text-left">Tag</th><th class="px-4 py-2 border-b text-left">Professors</th></tr></thead><tbody>`;
                        Object.entries(apiData.all_profs_by_tag).forEach(([tag, profs]) => {
                            tagTableHtml += `<tr><td class="px-4 py-2 border-b align-top font-semibold text-purple-700">${tag}</td><td class="px-4 py-2 border-b">${profs.length > 0 ? profs.map(p => `<span class='inline-block bg-purple-100 text-purple-800 rounded-full px-3 py-1 text-sm font-semibold mr-2 mb-1 tagwise-prof-hover' data-prof-name="${p.name}" data-prof-url="${p.base_url}" data-tag="${tag}"><a href="${p.base_url || '#'}" target="_blank" class="tagwise-profile-link text-inherit hover:underline" style="text-decoration:none;">${p.name}</a> <span class='text-xs text-gray-500'>(${p.department})</span><span class="tagwise-swap-icon hidden ml-2" style="vertical-align:middle; cursor:pointer;" title="Swap"><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='currentColor' class='inline' viewBox='0 0 16 16'><path d='M12.146 8.354a.5.5 0 0 0 .708-.708l-3-3a.5.5 0 0 0-.708.708L11.293 8H2.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z'/></svg></span></span>`).join(' ') : '<span class="text-gray-400">No professors found</span>'}</td></tr>`;
                        });
                        tagTableHtml += `</tbody></table></div>`;
                        
                        let tagTableContainer = document.getElementById('tagwise-table-container');
                        if (tagTableContainer) {
                            tagTableContainer.innerHTML = tagTableHtml;
                            tagTableContainer.classList.remove('hidden');
                        }
                        
                        // Add event listeners for hover effects on professor tags
                        Array.from(document.querySelectorAll('.tagwise-prof-hover')).forEach(el => {
                            el.addEventListener('mouseenter', function() {
                                this.querySelector('.tagwise-swap-icon').classList.remove('hidden');
                            });
                            el.addEventListener('mouseleave', function() {
                                this.querySelector('.tagwise-swap-icon').classList.add('hidden');
                            });
                        });
                        
                        // Add event listeners for swap icons
                        Array.from(document.querySelectorAll('.tagwise-swap-icon')).forEach(icon => {
                            icon.addEventListener('click', function(e) {
                                e.preventDefault();
                                e.stopPropagation();
                                const parent = this.closest('.tagwise-prof-hover');
                                const profName = parent.getAttribute('data-prof-name');
                                const tag = parent.getAttribute('data-tag');
                                let cardToSwap = null, oldProfName = null;
                                for (const [name, prof] of Object.entries(profMap)) {
                                    if (prof.tags && prof.tags.includes(tag)) {
                                        cardToSwap = prof;
                                        oldProfName = name;
                                        break;
                                    }
                                }
                                if (!cardToSwap || profName === oldProfName) return;
                                profMap[oldProfName].tags = profMap[oldProfName].tags.filter(tg => tg !== tag);
                                if (!profMap[profName]) {
                                    let dept = '', url = '';
                                    const found = (apiData.all_profs_by_tag[tag] || []).find(p => p.name === profName);
                                    if (found) { dept = found.department; url = found.base_url; }
                                    profMap[profName] = { name: profName, department: dept, base_url: url, tags: [] };
                                    const oldIdx = profOrder.indexOf(oldProfName);
                                    profOrder.splice(oldIdx + 1, 0, profName);
                                }
                                profMap[profName].tags = [...(profMap[profName].tags || []), tag];
                                if (profMap[oldProfName].tags.length === 0) {
                                    delete profMap[oldProfName];
                                    profOrder = profOrder.filter(n => n !== oldProfName);
                                }
                                profOrder = profOrder.filter((n, i, arr) => arr.indexOf(n) === i);
                                renderTeamCards();
                                setTimeout(attachDropdownListeners, 0);
                            });
                        });
                    }, 0);
                }
            }
            
            function attachDropdownListeners() {
                document.querySelectorAll('.alt-prof-select').forEach(sel => {
                    sel.removeEventListener('change', sel._dropdownListener);
                    sel._dropdownListener = function(e) {
                        let tag = this.getAttribute('data-tag');
                        const oldProfName = this.getAttribute('data-current-prof');
                        const tagsOfOldProf = JSON.parse(this.getAttribute('data-tags'));
                        const newProfName = this.value;
                        if (!newProfName) return;
                        
                        // Determine tags to move
                        const allProfsForTags = getProfsForTags(tagsOfOldProf);
                        const newProfCommonCount = allProfsForTags.find(p => p.name === newProfName)?.count || 1;
                        let tagsToMove = [];
                        if (newProfCommonCount >= 1 && tagsOfOldProf.length > 1) {
                            tagsToMove = tagsOfOldProf.filter(function(tg) {
                                if (!tg || tg.trim() === '') return false;
                                const allProfs = (apiData.all_profs_by_tag && apiData.all_profs_by_tag[tg]) || [];
                                return allProfs.some(p => p.name === newProfName);
                            });
                        } else {
                            // Only one tag in common: find it
                            tagsToMove = tagsOfOldProf;
                        }
                        
                        // Remove tags from old prof
                        profMap[oldProfName].tags = profMap[oldProfName].tags.filter(tg => !tagsToMove.includes(tg));
                        
                        // Add tags to new prof
                        if (!profMap[newProfName]) {
                            // Find department, url, position from all_profs_by_tag
                            let dept = '', url = '', position = '', google_scholar_url = '';
                            for (const tg of tagsToMove) {
                                if (!tg || tg.trim() === '') continue;
                                const found = (apiData.all_profs_by_tag && apiData.all_profs_by_tag[tg] || []).find(p => p.name === newProfName);
                                if (found) {
                                    dept = found.department;
                                    url = found.base_url;
                                    position = found.position || '';
                                    google_scholar_url = found.google_scholar_url || '';
                                    break;
                                }
                            }
                            profMap[newProfName] = {
                                name: newProfName,
                                department: dept,
                                base_url: url,
                                position: position,
                                google_scholar_url: google_scholar_url,
                                tags: []
                            };
                            const oldIdx = profOrder.indexOf(oldProfName);
                            profOrder.splice(oldIdx + 1, 0, newProfName);
                        }
                        
                        // Only assign non-empty tags, prevent duplicates
                        const filteredTagsToMove = tagsToMove.filter(tg => tg && tg.trim() !== '');
                        profMap[newProfName].tags = Array.from(new Set([...(profMap[newProfName].tags || []), ...filteredTagsToMove]));
                        
                        if (profMap[oldProfName].tags.length === 0) {
                            delete profMap[oldProfName];
                            profOrder = profOrder.filter(n => n !== oldProfName);
                        }
                        
                        profOrder = profOrder.filter((n, i, arr) => arr.indexOf(n) === i);
                        renderTeamCards();
                        setTimeout(attachDropdownListeners, 0);
                    };
                    sel.addEventListener('change', sel._dropdownListener);
                });
            }
            
            renderTeamCards();
            setTimeout(attachDropdownListeners, 0);
        } else {
            // Fallback for empty results
            if (currentResults.length === 0) {
                teamResultsSection.innerHTML = '<div class="bg-white p-8 rounded-lg shadow-md text-center col-span-full"><p class="text-gray-600 text-lg">No professors found matching your criteria.</p></div>';
                return;
            }
        }
    }

    /**
     * Render individual professors sorted by rank_score
     */
    function renderIndividualResults(professors) {
        if (!professors || professors.length === 0) {
            individualResultsSection.innerHTML = '<div class="bg-white p-8 rounded-lg shadow-md text-center"><p class="text-gray-600 text-lg">No individual professors found.</p></div>';
            return;
        }

        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">';
        
        professors.forEach((prof, index) => {
            const matchingTags = prof.matching_tags ? prof.matching_tags.slice(0, 5) : []; // Show max 5 tags
            const moreTagsCount = prof.matching_tags ? Math.max(0, prof.matching_tags.length - 5) : 0;
            
            html += `
                <div class="professor-card">
                    <div class="p-6 flex-grow">
                        <div class="flex justify-between items-start mb-4">
                            <div class="flex items-center">
                                <span class="bg-purple-600 text-white text-sm font-bold px-2 py-1 rounded-full mr-2">#${index + 1}</span>
                                <span class="bg-green-100 text-green-800 text-sm font-semibold px-2 py-1 rounded-full">
                                    Score: ${prof.rank_score}
                                </span>
                            </div>
                        </div>
                        
                        <h3 class="text-xl font-semibold text-gray-800 mb-2">${prof.name}</h3>
                        <p class="text-purple-700 mb-2">${prof.department}</p>
                        <p class="text-gray-600 mb-3">${prof.position || ''}</p>
                        
                        <div class="mb-4">
                            <div class="text-sm text-gray-600 mb-2">
                                <strong>Semantic:</strong> ${prof.semantic}% | 
                                <strong>Match:</strong> ${prof.weighted_match}%
                            </div>
                        </div>
                        
                        ${matchingTags.length > 0 ? `
                        <div class="mb-4">
                            <p class="text-sm font-semibold text-gray-700 mb-2">Matching Tags:</p>
                            <div class="flex flex-wrap gap-1">
                                ${matchingTags.map(tag => `<span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">${tag}</span>`).join('')}
                                ${moreTagsCount > 0 ? `<span class="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">+${moreTagsCount} more</span>` : ''}
                            </div>
                        </div>
                        ` : ''}
                        
                        <div class="flex gap-4">
                            <a href="${prof.base_url || '#'}" target="_blank" class="text-purple-700 hover:underline text-sm font-medium">Profile</a>
                            ${prof.google_scholar_url ? `<a href="${prof.google_scholar_url}" target="_blank" class="text-blue-700 hover:underline text-sm font-medium">Google Scholar</a>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        individualResultsSection.innerHTML = html;
    }

    // Initialize the UI
    teamResultsSection.innerHTML = '<div class="bg-white p-8 rounded-lg shadow-md text-center col-span-full"><p class="text-gray-600 text-lg">Enter your problem statement above to find professors...</p></div>';
});
