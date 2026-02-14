// 전역 변수
let selectedCompany = null;
let currentFinancialData = null;
let charts = {
    balanceSheet: null,
    incomeStatement: null,
    trend: null
};

// DOM 요소
const elements = {
    companySearch: document.getElementById('company-search'),
    searchResults: document.getElementById('search-results'),
    searchBtn: document.getElementById('search-btn'),
    bsnsYear: document.getElementById('bsns-year'),
    reprtCode: document.getElementById('reprt-code'),
    fsType: document.getElementById('fs-type'),
    companyInfo: document.getElementById('company-info'),
    companyName: document.getElementById('company-name'),
    corpCode: document.getElementById('corp-code'),
    stockCode: document.getElementById('stock-code'),
    loading: document.getElementById('loading'),
    errorMessage: document.getElementById('error-message'),
    chartsContainer: document.getElementById('charts-container'),
    tableBody: document.getElementById('table-body'),
    aiExplainBtn: document.getElementById('ai-explain-btn'),
    aiExplanation: document.getElementById('ai-explanation'),
    aiError: document.getElementById('ai-error'),
    stockChartSection: document.getElementById('stock-chart-section'),
    stockChartImage: document.getElementById('stock-chart-image')
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initializeYearSelector();
    attachEventListeners();
});

/**
 * 연도 선택기 초기화 (2015년부터 현재까지)
 */
function initializeYearSelector() {
    const currentYear = new Date().getFullYear();
    const startYear = 2015;

    for (let year = currentYear; year >= startYear; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year + '년';
        elements.bsnsYear.appendChild(option);
    }
}

/**
 * 이벤트 리스너 등록
 */
function attachEventListeners() {
    // 회사 검색 (150ms debounce로 검색 속도 개선)
    elements.companySearch.addEventListener('input', debounce(handleCompanySearch, 150));

    // 검색 결과 외부 클릭 시 닫기
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-box')) {
            elements.searchResults.classList.remove('active');
        }
    });

    // 조회 버튼
    elements.searchBtn.addEventListener('click', handleSearchSubmit);

    // 탭 버튼
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabChange);
    });

    // AI 설명 버튼
    elements.aiExplainBtn.addEventListener('click', handleAIExplain);
}

/**
 * Debounce 유틸리티 함수
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 회사 검색 처리 (검색 결과 50개로 증가)
 */
async function handleCompanySearch(e) {
    const keyword = e.target.value.trim();

    if (keyword.length < 2) {
        elements.searchResults.classList.remove('active');
        return;
    }

    try {
        // 검색 결과를 50개로 증가하여 더 많은 회사를 찾을 수 있도록 개선
        const response = await fetch(`/api/search?q=${encodeURIComponent(keyword)}&limit=50`);
        const companies = await response.json();

        if (companies.error) {
            console.error('검색 오류:', companies.error);
            return;
        }

        displaySearchResults(companies);

    } catch (error) {
        console.error('검색 요청 실패:', error);
    }
}

/**
 * 검색 결과 표시 (스크롤 가능, 결과 개수 표시)
 */
function displaySearchResults(companies) {
    if (companies.length === 0) {
        elements.searchResults.innerHTML = '<div class="search-result-item no-result">검색 결과가 없습니다.</div>';
        elements.searchResults.classList.add('active');
        return;
    }

    // 결과 개수 표시 헤더 추가
    const headerHtml = `
        <div class="search-results-header">
            <span class="results-count">검색 결과: ${companies.length}개</span>
            ${companies.length >= 50 ? '<span class="results-hint">⬇️ 스크롤하여 더 보기</span>' : ''}
        </div>
    `;

    const itemsHtml = companies.map(company => `
        <div class="search-result-item" data-company='${JSON.stringify(company)}'>
            <span class="result-name">${company.corp_name}</span>
            ${company.stock_code ? `<span class="result-code">(${company.stock_code})</span>` : ''}
            <span class="result-badge ${company.is_listed ? 'badge-listed' : 'badge-unlisted'}">
                ${company.is_listed ? '상장' : '비상장'}
            </span>
        </div>
    `).join('');

    elements.searchResults.innerHTML = headerHtml + itemsHtml;
    elements.searchResults.classList.add('active');

    // 검색 결과 클릭 이벤트
    elements.searchResults.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', handleCompanySelect);
    });
}

/**
 * 회사 선택 처리
 */
function handleCompanySelect(e) {
    const companyData = e.currentTarget.dataset.company;
    if (!companyData) return;

    selectedCompany = JSON.parse(companyData);

    // UI 업데이트
    elements.companySearch.value = selectedCompany.corp_name;
    elements.searchResults.classList.remove('active');
    elements.searchBtn.disabled = false;

    // 회사 정보 표시
    elements.companyInfo.style.display = 'block';
    elements.companyName.textContent = selectedCompany.corp_name;
    elements.corpCode.textContent = selectedCompany.corp_code;
    elements.stockCode.textContent = selectedCompany.stock_code || '비상장';

    // 주식 차트 준비 (상장사인 경우에만)
    if (selectedCompany.stock_code) {
        const chartUrl = `https://ssl.pstatic.net/imgfinance/chart/item/area/year3/${selectedCompany.stock_code}.png?sid=${new Date().getTime()}`;
        elements.stockChartImage.src = chartUrl;
    }
}

/**
 * 조회 버튼 클릭 처리
 */
async function handleSearchSubmit() {
    if (!selectedCompany) return;

    const bsnsYear = elements.bsnsYear.value;
    const reprtCode = elements.reprtCode.value;

    // UI 초기화
    showLoading();
    hideError();
    elements.chartsContainer.style.display = 'none';

    try {
        const response = await fetch(
            `/api/financial-statement?corp_code=${selectedCompany.corp_code}&bsns_year=${bsnsYear}&reprt_code=${reprtCode}`
        );

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        currentFinancialData = data;
        displayFinancialData(data);

    } catch (error) {
        showError('데이터를 가져오는 중 오류가 발생했습니다: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 재무 데이터 표시 (5개 연도)
 */
function displayFinancialData(data) {
    // 차트 생성
    createBalanceSheetChart(data);
    createIncomeStatementChart(data);
    createTrendChart(data);

    // 테이블 표시
    displayDataTable(data, 'balance-sheet');

    // AI 설명 초기화
    elements.aiExplanation.style.display = 'none';
    elements.aiError.style.display = 'none';

    // 차트 컨테이너 표시
    elements.chartsContainer.style.display = 'block';

    // 주식 차트 섹션 표시 여부 결정
    if (selectedCompany && selectedCompany.stock_code) {
        elements.stockChartSection.style.display = 'block';
    } else {
        elements.stockChartSection.style.display = 'none';
    }

    // 차트로 스크롤
    elements.chartsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 창 크기 조절 시 차트 리사이즈 처리 (필요한 경우)
window.addEventListener('resize', debounce(() => {
    Object.values(charts).forEach(chart => {
        if (chart) chart.resize();
    });
}, 250));

/**
 * 재무상태표 차트 생성 (5개 연도)
 */
function createBalanceSheetChart(data) {
    const ctx = document.getElementById('balance-sheet-chart');

    // 기존 차트 제거
    if (charts.balanceSheet) {
        charts.balanceSheet.destroy();
    }

    const fsType = elements.fsType.value;

    // 통합 데이터에서 추출
    if (!data.balance_sheet || !data.balance_sheet[fsType]) {
        console.warn('재무상태표 데이터가 없습니다.');
        return;
    }

    const bsData = data.balance_sheet[fsType];
    const periods = data.periods || [];

    // 주요 계정별 데이터셋 생성
    const colors = [
        'rgba(79, 70, 229, 0.7)',   // 보라
        'rgba(16, 185, 129, 0.7)',  // 초록
        'rgba(245, 158, 11, 0.7)',  // 주황
        'rgba(239, 68, 68, 0.7)',   // 빨강
        'rgba(59, 130, 246, 0.7)'   // 파랑
    ];

    const datasets = [];
    const accounts = ['자산총계', '부채총계', '자본총계'];

    // 각 계정별로 데이터셋 생성
    accounts.forEach((account, idx) => {
        const accountData = bsData[account] || [];

        datasets.push({
            label: account,
            data: accountData.map(item => item.amount),
            backgroundColor: colors[idx % colors.length],
            borderColor: colors[idx % colors.length].replace('0.7', '1'),
            borderWidth: 2
        });
    });

    // 라벨 생성 (기수와 연도)
    const labels = periods.map(p => p.label);

    charts.balanceSheet = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + formatAmount(context.parsed.y) + '원';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return formatAmount(value) + '원';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 손익계산서 차트 생성 (5개 연도)
 */
function createIncomeStatementChart(data) {
    const ctx = document.getElementById('income-statement-chart');

    // 기존 차트 제거
    if (charts.incomeStatement) {
        charts.incomeStatement.destroy();
    }

    const fsType = elements.fsType.value;

    // 통합 데이터에서 추출
    if (!data.income_statement || !data.income_statement[fsType]) {
        console.warn('손익계산서 데이터가 없습니다.');
        return;
    }

    const isData = data.income_statement[fsType];
    const periods = data.periods || [];

    // 주요 계정별 데이터셋 생성
    const colors = [
        'rgba(245, 158, 11, 0.7)',  // 주황
        'rgba(59, 130, 246, 0.7)',  // 파랑
        'rgba(16, 185, 129, 0.7)',  // 초록
        'rgba(239, 68, 68, 0.7)',   // 빨강
        'rgba(147, 51, 234, 0.7)'   // 보라
    ];

    const datasets = [];
    const accounts = ['매출액', '영업이익', '당기순이익(손실)'];

    // 각 계정별로 데이터셋 생성
    accounts.forEach((account, idx) => {
        const accountData = isData[account] || [];

        datasets.push({
            label: account,
            data: accountData.map(item => item.amount),
            backgroundColor: colors[idx % colors.length],
            borderColor: colors[idx % colors.length].replace('0.7', '1'),
            borderWidth: 2
        });
    });

    // 라벨 생성 (기수와 연도)
    const labels = periods.map(p => p.label);

    charts.incomeStatement = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + formatAmount(context.parsed.y) + '원';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return formatAmount(value) + '원';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 추세 차트 생성 (5개 연도)
 */
function createTrendChart(data) {
    const ctx = document.getElementById('trend-chart');
    const fsType = elements.fsType.value;

    // 기존 차트 제거
    if (charts.trend) {
        charts.trend.destroy();
    }

    // 통합 데이터에서 추출
    if (!data.income_statement || !data.income_statement[fsType]) {
        console.warn('추세 차트 데이터가 없습니다.');
        return;
    }

    const isData = data.income_statement[fsType];
    const periods = data.periods || [];

    // 라벨 생성
    const labels = periods.map(p => p.label);

    // 매출액과 당기순이익 데이터 추출
    const revenueData = (isData['매출액'] || []).map(item => item.amount);
    const netIncomeData = (isData['당기순이익(손실)'] || []).map(item => item.amount);
    const operatingIncomeData = (isData['영업이익'] || []).map(item => item.amount);

    charts.trend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '매출액',
                    data: revenueData,
                    borderColor: 'rgba(79, 70, 229, 1)',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: '영업이익',
                    data: operatingIncomeData,
                    borderColor: 'rgba(245, 158, 11, 1)',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7
                },
                {
                    label: '당기순이익',
                    data: netIncomeData,
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + formatAmount(context.parsed.y) + '원';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return formatAmount(value) + '원';
                        }
                    }
                }
            }
        }
    });
}

/**
 * 데이터 테이블 표시 (5개 연도)
 */
function displayDataTable(data, tableType) {
    if (!data || !data.periods || data.periods.length === 0) {
        elements.tableBody.innerHTML = '<tr><td colspan="' + (data.periods?.length + 1 || 6) + '">데이터가 없습니다.</td></tr>';
        return;
    }

    const fsType = elements.fsType.value;
    const periods = data.periods;

    // 테이블 헤더 업데이트
    const tableHeader = document.querySelector('#data-table thead tr');
    tableHeader.innerHTML = `
        <th>계정명</th>
        ${periods.map(p => `<th class="amount-col">${p.label}</th>`).join('')}
    `;

    // 데이터 타입에 따라 계정과목 선택
    let accountsData = [];
    let accounts = [];

    if (tableType === 'balance-sheet') {
        accountsData = data.balance_sheet[fsType];
        accounts = ['자산총계', '유동자산', '비유동자산', '부채총계', '유동부채', '비유동부채', '자본총계'];
    } else {
        accountsData = data.income_statement[fsType];
        accounts = ['매출액', '영업이익', '법인세차감전 순이익', '당기순이익(손실)'];
    }

    // 테이블 바디 생성
    elements.tableBody.innerHTML = accounts.map(account => {
        const accountData = accountsData[account] || [];

        return `
            <tr>
                <td><strong>${account}</strong></td>
                ${accountData.map(item => {
            const formattedAmount = formatAmount(item.amount);
            const isNegative = item.amount < 0;
            const colorClass = isNegative ? 'amount-negative' : '';
            return `<td class="amount ${colorClass}">${formattedAmount}</td>`;
        }).join('')}
                ${Array(periods.length - accountData.length).fill('<td class="amount">-</td>').join('')}
            </tr>
        `;
    }).join('');
}

/**
 * 탭 변경 처리
 */
function handleTabChange(e) {
    const tabName = e.target.dataset.tab;

    // 탭 버튼 활성화
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');

    // 테이블 업데이트
    if (currentFinancialData) {
        displayDataTable(currentFinancialData, tabName);
    }
}

/**
 * 금액 포맷팅 (억/조 단위로 변환)
 */
function formatAmount(amount) {
    if (!amount || amount === 0) return '0';

    const absAmount = Math.abs(amount);
    const isNegative = amount < 0;
    const sign = isNegative ? '-' : '';

    // 조 단위 (1조 = 1,000,000,000,000)
    if (absAmount >= 1000000000000) {
        const trillion = absAmount / 1000000000000;
        return sign + trillion.toLocaleString('ko-KR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }) + ' 조';
    }

    // 억 단위 (1억 = 100,000,000)
    if (absAmount >= 100000000) {
        const billion = absAmount / 100000000;
        return sign + billion.toLocaleString('ko-KR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }) + ' 억';
    }

    // 만 단위 (1만 = 10,000)
    if (absAmount >= 10000) {
        const tenThousand = absAmount / 10000;
        return sign + tenThousand.toLocaleString('ko-KR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }) + ' 만';
    }

    return sign + absAmount.toLocaleString('ko-KR');
}

/**
 * 로딩 표시
 */
function showLoading() {
    elements.loading.style.display = 'block';
    elements.searchBtn.querySelector('.btn-text').textContent = '조회 중...';
    elements.searchBtn.querySelector('.loader').style.display = 'inline-block';
    elements.searchBtn.disabled = true;
}

/**
 * 로딩 숨김
 */
function hideLoading() {
    elements.loading.style.display = 'none';
    elements.searchBtn.querySelector('.btn-text').textContent = '조회하기';
    elements.searchBtn.querySelector('.loader').style.display = 'none';
    elements.searchBtn.disabled = false;
}

/**
 * 에러 표시
 */
function showError(message) {
    elements.errorMessage.textContent = '⚠️ ' + message;
    elements.errorMessage.style.display = 'block';
}

/**
 * 에러 숨김
 */
function hideError() {
    elements.errorMessage.style.display = 'none';
}

/**
 * AI 설명 요청 처리
 */
async function handleAIExplain() {
    if (!currentFinancialData || !selectedCompany) {
        showAIError('먼저 재무제표 데이터를 조회해주세요.');
        return;
    }

    // UI 업데이트
    showAILoading();
    hideAIError();
    elements.aiExplanation.style.display = 'none';

    try {
        console.log('🤖 AI 설명 요청 시작...');

        const response = await fetch('/api/explain-financial-statement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                financial_data: currentFinancialData,
                company_name: selectedCompany.corp_name,
                fs_type: elements.fsType.value
            }),
            // 타임아웃 설정 (50초 - 서버 재시도 로직 대응)
            signal: AbortSignal.timeout(50000)
        });

        console.log(`📡 응답 상태: ${response.status} ${response.statusText}`);

        // 응답 상태 확인
        if (!response.ok) {
            // JSON 파싱 시도
            let errorData;
            try {
                const text = await response.text();
                console.log('📄 응답 내용:', text.substring(0, 200));

                // JSON 파싱 시도
                try {
                    errorData = JSON.parse(text);
                } catch (jsonError) {
                    // JSON이 아닌 경우 (HTML 에러 페이지 등)
                    throw new Error(`서버 오류 (${response.status}): JSON 형식이 아닌 응답을 받았습니다.`);
                }
            } catch (textError) {
                throw new Error(`서버 오류 (${response.status}): 응답을 읽을 수 없습니다.`);
            }

            // 에러 타입별 메시지
            const errorMsg = errorData.error || '알 수 없는 오류가 발생했습니다.';
            const errorDetail = errorData.detail ? `\n\n상세: ${errorData.detail}` : '';

            throw new Error(errorMsg + errorDetail);
        }

        // 정상 응답 처리
        let data;
        try {
            const text = await response.text();

            // 빈 응답 체크
            if (!text || text.trim().length === 0) {
                throw new Error('서버에서 빈 응답을 받았습니다.');
            }

            // JSON 파싱
            data = JSON.parse(text);
            console.log('✅ JSON 파싱 성공');

        } catch (parseError) {
            console.error('❌ JSON 파싱 오류:', parseError);
            throw new Error('서버 응답을 처리할 수 없습니다. 다시 시도해주세요.');
        }

        // 데이터 검증
        if (data.error) {
            const errorMsg = data.error;
            const errorDetail = data.detail ? `\n\n${data.detail}` : '';
            showAIError(errorMsg + errorDetail);
            return;
        }

        if (!data.explanation) {
            showAIError('AI 설명이 생성되지 않았습니다. 다시 시도해주세요.');
            return;
        }

        // 재시도 횟수 로깅 (디버깅용)
        if (data.retry_count > 0) {
            console.log(`✅ AI 설명 생성 완료 (${data.retry_count}번 재시도 후 성공)`);
        } else {
            console.log('✅ AI 설명 생성 완료');
        }

        displayAIExplanation(data.explanation);

    } catch (error) {
        console.error('❌ AI 설명 생성 오류:', error);

        // 에러 타입별 메시지
        let errorMessage;

        if (error.name === 'AbortError' || error.name === 'TimeoutError') {
            errorMessage = '⏱️ AI 응답 시간이 초과되었습니다.\n\n서버가 자동으로 재시도했지만 실패했습니다. 네트워크 상태를 확인하고 잠시 후 다시 시도해주세요.';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = '🌐 네트워크 연결에 문제가 있습니다.\n\n인터넷 연결을 확인하고 다시 시도해주세요.';
        } else if (error.message.includes('JSON')) {
            errorMessage = '⚠️ 서버 응답 형식 오류\n\n' + error.message;
        } else {
            errorMessage = '❌ ' + error.message;
        }

        showAIError(errorMessage);

    } finally {
        hideAILoading();
    }
}

/**
 * AI 설명 표시 (초단순 안전 렌더링 - 텍스트 손실 없음!)
 */
function displayAIExplanation(explanation) {
    const content = elements.aiExplanation.querySelector('.explanation-content');

    console.log('='.repeat(80));
    console.log('📝 AI 설명 렌더링 시작');
    console.log('📏 원본 길이:', explanation.length, '자');
    console.log('📄 원본 처음 200자:', explanation.substring(0, 200));
    console.log('📄 원본 마지막 200자:', explanation.substring(explanation.length - 200));

    // ✨ 초단순 방식: textContent로 먼저 삽입 (100% 안전)
    // 이렇게 하면 모든 텍스트가 손실 없이 DOM에 들어감!
    content.textContent = explanation;

    // 그 다음 innerHTML을 사용해서 마크다운만 변환
    // 이미 DOM에 안전하게 들어간 텍스트를 가져와서 변환
    let safeText = content.innerHTML;  // 이미 이스케이프된 안전한 HTML

    console.log('🔒 안전하게 이스케이프된 길이:', safeText.length);

    // **굵은글씨** 변환 (이미 이스케이프된 상태에서)
    let boldCount = 0;
    safeText = safeText.replace(/\*\*([^*]+)\*\*/g, function (match, content) {
        boldCount++;
        return '<strong>' + content + '</strong>';
    });

    console.log('🔤 굵은글씨 변환:', boldCount + '개');

    // 줄바꿈 변환 (\n\n → 단락, \n → <br>)
    safeText = safeText
        .replace(/\n\n+/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // 단락으로 감싸기
    safeText = '<p>' + safeText + '</p>';

    // 빈 단락 제거
    safeText = safeText.replace(/<p>\s*<\/p>/g, '');

    console.log('✅ 최종 HTML 길이:', safeText.length);
    console.log('🎨 최종 처음 300자:', safeText.substring(0, 300));
    console.log('🎨 최종 마지막 300자:', safeText.substring(safeText.length - 300));

    // 최종 HTML 삽입
    content.innerHTML = safeText;
    elements.aiExplanation.style.display = 'block';

    // 검증: DOM에 실제로 들어간 텍스트 확인
    const finalText = content.textContent;
    console.log('🌐 DOM 최종 렌더링 길이:', finalText.length, '자');
    console.log('🌐 DOM 처음 200자:', finalText.substring(0, 200));
    console.log('🌐 DOM 마지막 200자:', finalText.substring(finalText.length - 200));

    // 원본과 비교
    const originalLength = explanation.length;
    const finalLength = finalText.length;
    const diff = originalLength - finalLength;

    if (Math.abs(diff) > 10) {
        console.warn('⚠️ 원본과 렌더링 길이 차이:', diff, '자');
        console.warn('   원본:', originalLength, '자');
        console.warn('   DOM:', finalLength, '자');
    } else {
        console.log('✅ 원본과 DOM 길이 일치 확인 (차이:', diff, '자)');
    }

    console.log('='.repeat(80));

    // 부드럽게 스크롤
    setTimeout(() => {
        elements.aiExplanation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

/**
 * AI 로딩 표시
 */
function showAILoading() {
    const btn = elements.aiExplainBtn;
    btn.querySelector('.btn-text').textContent = 'AI 분석 중...';
    btn.querySelector('.ai-loader').style.display = 'inline-block';
    btn.disabled = true;
}

/**
 * AI 로딩 숨김
 */
function hideAILoading() {
    const btn = elements.aiExplainBtn;
    btn.querySelector('.btn-text').textContent = 'AI로 쉽게 설명받기';
    btn.querySelector('.ai-loader').style.display = 'none';
    btn.disabled = false;
}

/**
 * AI 에러 표시
 */
function showAIError(message) {
    elements.aiError.textContent = '⚠️ ' + message;
    elements.aiError.style.display = 'block';
}

/**
 * AI 에러 숨김
 */
function hideAIError() {
    elements.aiError.style.display = 'none';
}

// 재무제표 구분 변경 시 차트 업데이트
elements.fsType.addEventListener('change', () => {
    if (currentFinancialData) {
        displayFinancialData(currentFinancialData);
    }
});

