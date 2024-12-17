var baseURL = window.location.origin;
var marketCharts = {};
const domCache = {};

/**
 * Transforms raw data into a Google Chart and renders it on the page.
 *
 * @param {string} marketId - The ID of the market.
 * @param {Array<Array<number>>} rawData - An array of arrays, where each inner array represents a data point with [x, y] coordinates.
 */
function chartDataTransform(marketId, rawData) {

    const containerElement = document.getElementById('chart_div_' + marketId);
    let xRange = 1000;
    const data = new google.visualization.DataTable();
    data.addColumn('number', 'X');
    data.addColumn('number', 'Yes');

    for (const point of rawData) {
        data.addRow([point[0], point[1]])
    };

    const lastData = rawData.at(-1);
    const maxXPoint = lastData[0];

    xRange = maxXPoint * 1.1 >= xRange ? maxXPoint * 1.25 : xRange;

    marketCharts[marketId] = {}
    marketCharts[marketId].data = data;

    var options = {
        hAxis: {
            title: 'Time(seconds)',
            viewWindow: {
                max: xRange
            }
        },
        vAxis: {
            title: 'Price',
            viewWindow: {
                min: 0,
                max: 1
            }
        },
        width: containerElement.clientWidth,
        height: 300
    };

    marketCharts[marketId]['options'] = options;

    const chart = new google.visualization.LineChart(document.getElementById('chart_div_' + marketId));
    marketCharts[marketId]['chart'] = chart;
    chart.draw(data, options);
}


/**
 * Updates the market chart with the given price and timestamp.
 *
 * @param {string} marketId - The ID of the market.
 * @param {number} price - The current price.
 * @param {number} price_et - The timestamp of the price.
 */
function updateMarketChart(marketId, price, price_et) {
    if(marketCharts[marketId] === undefined){
        return;
    }
    var data = marketCharts[marketId].data;
    data.addRow([price_et, price]);

    var options = marketCharts[marketId].options;
    var xRange = options.hAxis.viewWindow.max;
    var newXRange = price_et * 1.1 >= xRange ? price_et * 1.25 : xRange;

    options.hAxis.viewWindow.max = newXRange;

    var chart = marketCharts[marketId].chart;
    chart.draw(data, options);
}


/**
 * Fetches and updates prices for market instruments.
 *
 * This function retrieves price data from an API endpoint and updates the corresponding HTML elements with the latest prices.
 */
async function updatePrices() {
    try {
        const prices = await fetch(`${baseURL}/api/instruments`);
        const priceData = await prices.json()
        for (const p of priceData) {
            const elementId = p.id + '_price';
            const elHTML = document.getElementById(elementId);
            if(elHTML === null){
                continue;
            }
            element.textContent = p.price;
        }
    } catch (error) {
        console.error('Error fetching prices:', error);
    }
}


/**
 * Updates the content of an HTML element.
 *
 * This function caches DOM elements to optimize performance.
 * If the element is not already cached, it retrieves it from the DOM.
 *
 * @param {string} elId - The ID of the element to update.
 * @param {string} elContent - The new content for the element.
 */
function updateHTML(elId, elContent) {
    let element = domCache[elId];
    if (!element) {
        element = document.getElementById(elId);
        if (element === null) {
            return;
        }
        domCache[elId] = element;
    }
    element.textContent = elContent;
}


/**
 * Sets the price for a market instrument in the corresponding HTML element.
 *
 * @param {string} instrId - The ID of the instrument.
 * @param {number} price - The price to display.
 */
function setInstrPrice(instrId, price) {
    const elId = instrId + '_price';
    updateHTML(elId, price.toFixed(2));
}


/**
 * Sets the number of trades for a market in the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @param {number} nTrades - The number of trades to display.
 */
function setMarketTrades(marketId, nTrades) {
    const elId = marketId + '_trades';
    updateHTML(elId, nTrades); 
}


/**
 * Retrieves the status value of a market from the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @returns {string|undefined} The status value of the market, or undefined if the element is not found.
 */
function getMarketStatusVal(marketId) {
    const elId = marketId + '_status';
    const element = document.getElementById(elId); 
    if (element === null) {
        return; 
    }
    return element.innerHTML;
}


/**
 * Sets the status of a market in the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} status - The status to display.
 */
function setMarketStatus(marketId, status) {
    const elId = marketId + '_status';
    updateHTML(elId, status); 
}


/**
 * Sets the CSS class of the HTML element that displays the status of a market.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} style - The CSS class name to apply.
 */
function setMarketStatusStyle(marketId, style) {
    const elId = marketId + '_status';
    const element = document.getElementById(elId);
    if (element === null) {
        return;
    }
    element.className = style;
}


/**
 * Sets the countdown value for a market in the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} value - The countdown value to display.
 */
function setCountDownVal(marketId, value) {
    const elId = marketId + '_countdown_val';
    updateHTML(elId, value); 
}


/**
 * Sets the countdown label for a market in the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} label - The countdown label to display.
 */
function setCountDownLabel(marketId, label) {
    const elId = marketId + '_countdown_label';
    updateHTML(elId, label);
}


/**
 * Sets the user's number of trades for a market in the corresponding HTML element.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} value - The number of user trades to display.
 */
function setUserTrades(marketId, value) {
    const elId = marketId + '_user_trades';
    updateHTML(elId, value); 
}


/**
 * Sets the CSS class of the HTML element that displays the countdown for a market.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} style - The CSS class name to apply.
 */
function setCountDownStyle(marketId, style) {
    const elId = marketId + '_countdown';
    const element = document.getElementById(elId);
    if (element === null) {
        return;
    }
    element.className = style;
}


/**
 * Retrieves trade buttons for a specific market from the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @returns {NodeList|null} - A NodeList of trade buttons or null if no buttons are found.
 */
function getMarketTradeButtons(marketId) {
    const marketElId = `${marketId}_market`;
    const marketElement = document.getElementById(marketElId);
    if(marketElement === null){
        return null;
    }
    const tradeButtons = marketElement.querySelectorAll("button[type='trade_button']");
    return tradeButtons;
}


/**
 * Retrieves position rows for a specific market from the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @returns {NodeList|null} - A NodeList of position rows or null if no rows are found.
 */
function getPositionRows(marketId) {
    const marketElId = `${marketId}_market`;
    const marketElement = document.getElementById(marketElId);
    if(marketElement === null){
        return null;
    }
    const positionRows = marketElement.querySelectorAll("tr[name = 'position_row']");
    return positionRows;
}


/**
 * Retrieves payout rows for a specific market from the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @returns {NodeList|null} - A NodeList of payout rows or null if no rows are found.
 */
function getPayoutRows(marketId) {
    const marketElId = `${marketId}_market`;
    const marketElement = document.getElementById(marketElId);
    if(marketElement === null){
        return null;
    }
    const payoutRows = marketElement.querySelectorAll("tr[name = 'payout_row']");
    return payoutRows;
}


/**
 * Retrieves the available funds for a specific market from the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @returns {number|null} - The available funds as a number, or null if the element is not found.
 */
function getAvailFunds(marketId) {
    const availableFundsElementId = `${marketId}_af`;
    const availableFundsElement = document.getElementById(availableFundsElementId);
    if(availableFundsElement === null){
        return null;
    }
    const availableFunds = availableFundsElement.innerHTML;
    return +availableFunds; 
}

/**
 * Sets the available funds for a specific market in the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @param {number} value - The value to set as available funds.
 */
function setAvailFunds(marketId, value) {
    const availableFundsElementName = `${marketId}_af`;
    const availableFundsElements = document.querySelectorAll(`[name = "${availableFundsElementName}"]`);
    availableFundsElements.forEach((el) => { el.innerHTML = value.toFixed(2) });
}

/**
 * Sets the title of the payout section for a specific market in the DOM using updateHTML.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} title - The title to set for the payout section.
 */
function setPayoutTitle(marketId, title) {
    const payoutTitleElementId = `${marketId}_payout_title`;
    updateHTML(payoutTitleElementId, title); 
}


/**
 * Sets the position values for a specific instrument in a market within the DOM.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} instrName - The name of the instrument.
 * @param {number} value - The value to set for the positions.
 */
function setPositions(marketId, instrName, value) {
    // Update all elements displaying positions for the given instrument with the specified value
    const marketElementId = `${marketId}_market`;
    const marketElement = document.getElementById(marketElementId);
    if (marketElement === null) {
        return;
    }
    const positionAttributeName = `${instrName}_pos`;
    const positionElements = marketElement.querySelectorAll(`[${positionAttributeName}]`);
    positionElements.forEach((el) => { el.innerHTML = value.toFixed(0) });
}


/**
 * Sets the payout value for a specific instrument in the DOM using updateHTML.
 *
 * @param {string} instrId - The ID of the instrument.
 * @param {number} value - The payout value to set.
 */
function setPayout(instrId, value) {
    const payoutElementId = `${instrId}_payout`;
    updateHTML(payoutElementId, value.toFixed(2)); 
}


/**
 * Sets the payout result for a specific instrument in the DOM using updateHTML.
 *
 * @param {string} instrId - The ID of the instrument.
 * @param {string} value - The payout result value to set.
 */
function setPayoutResult(instrId, value) {
    const payoutResultElementId = `${instrId}_payout_result`;
    updateHTML(payoutResultElementId, value);
}


/**
 * Sets the CSS class name of a payout row element based on a given value.
 *
 * @param {string} instrId - The ID of the instrument.
 * @param {string} value - The value used to determine the class name.
 */
function setPayoutRowStyle(instrId, value) {
    // Update the class name of the payout row element
    const payoutRowElementId = `${instrId}_payout_row`;
    const payoutRowClassName = value.toLowerCase() + '-row';
    const payoutRowElement = document.getElementById(payoutRowElementId);
    if (payoutRowElement === null) {
      return;
    }
    payoutRowElement.className = payoutRowClassName;
}


/**
 * Activates or deactivates trade buttons (BUY/SELL) in a position row based on available funds, prices, positions.
 *
 * @param {HTMLTableRowElement} positionRow - The table row element representing a position.
 * @param {number} availFunds - The available funds for trading.
 */
function activatePositionTradeButtons(positionRow, availFunds) {
    const positionSize = positionRow.querySelector('[name="position"]').innerHTML;
    const price = positionRow.querySelector('[name="price"]').innerHTML;
    const buyButton = positionRow.querySelector('[name="BUY"]');
    const sellButton = positionRow.querySelector('[name="SELL"]');
    
    const activeBuy = +price <= availFunds;  
    const activeSell = +positionSize > 0;    

    buyButton.className = activeBuy ? 'table-button table-button-buy' : 'table-button table-button-inactive';
    sellButton.className = activeSell ? 'table-button table-button-sell' : 'table-button table-button-inactive';
}


/**
 * Activates trade buttons for all positions within a specific market.
 *
 * @param {string} marketId - The ID of the market.
 */
function activateMarketTradeButtons(marketId) {
    const positionRows = getPositionRows(marketId);
    if(positionRows === null){
        return;
    }
    const availFunds = getAvailFunds(marketId);
    // Iterate through each position row and activate its trade buttons
    positionRows.forEach((el) => { 
        activatePositionTradeButtons(el, availFunds);
    });
}


/**
 * Deactivates the trade buttons for a specific market.
 *
 * @param {string} marketId - The ID of the market.
 */
function deactivateMarketTradeButtons(marketId) {
    const tradeButtons = getMarketTradeButtons(marketId);
    if (tradeButtons === null) {
        return;
    }
    tradeButtons.forEach((el) => {
        el.className = "table-button table-button-inactive"
    });
}


/**
 * Updates the market instruments data.
 *
 * Fetches market instrument data from the server, iterates through each market, and updates the UI based on the market status.
 * For 'OPEN' markets, it updates the market trades, instrument prices, and market chart.
 * For 'SETTLED' or 'CLOSED' markets, it updates the payout results and row styles.
 */
async function updMarketInstruments() {
    const response = await fetch(`${baseURL}/api/market_instruments`);
    const data = await response.json()

    for (m of data) {
        const marketStatus = m.status;
        updMarketStatus(m.id, marketStatus);
        const marketTrades = m.n_exec_trades;
        setMarketTrades(m.id, marketTrades);
        if (marketStatus === 'OPEN') {
            tradedInstruments = m.instruments.filter((instr) => instr.name != 'Cash');
            for (instr of tradedInstruments) {
                setInstrPrice(instr.id, instr.price);
                if (instr.name === 'Yes') {
                    updateMarketChart(m.id, instr.price, instr.current_mt);
                }
            }
        }
        else if (marketStatus === 'SETTLED' || marketStatus === 'CLOSED') {
            tradedInstruments = m.instruments.filter((instr) => instr.name != 'Cash');
            for (instr of tradedInstruments) {
                setPayoutResult(instr.id, instr.outcome_status);
                setPayoutRowStyle(instr.id, instr.outcome_status);
            }
        }
    }
}


/**
 * Updates the countdown label and style based on the market status.
 *
 * @param {string} marketId - The ID of the market.
 */
function updCountDownLabel(marketId) {
    var status = getMarketStatusVal(marketId);

    switch (status) {
        case 'OPEN':
        case 'SUSPENDED':
            setCountDownStyle(marketId, 'market-header-cdown');
            setCountDownLabel(marketId, "Time To Close")
            break;
        case 'PENDING':
            setCountDownStyle(marketId, 'market-header-cdown');
            setCountDownLabel(marketId, "Time To Open")
            break;
        case 'CLOSED':
        case 'SETTLED':
            setCountDownStyle(marketId, 'market-header-cdown-hide');
            break;
    }
}


/**
 * Updates the market status and related UI elements.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} newStatus - The new status of the market.
 */
function updMarketStatus(marketId, newStatus) {
    var currStatus = getMarketStatusVal(marketId);
    if (currStatus === null || currStatus === newStatus) {
        return;
    }
    var statusClass = 'market-header-status-' + newStatus.toLowerCase();
    setMarketStatus(marketId, newStatus);
    setMarketStatusStyle(marketId, 'market-header-status ' + statusClass);
    if (newStatus === "OPEN") {
      activateMarketTradeButtons(marketId);
    } else {
      deactivateMarketTradeButtons(marketId);
    }
    setPayoutTitle(marketId, newStatus === "SETTLED" ? 'Payout' : 'Projected Payout');
    updCountDownLabel(marketId);
}


/**
 * Updates the market countdown timer using the Luxon library.
 *
 * Converts the opening and closing date/time strings to Luxon DateTime objects,
 * calculates the time difference based on the market status, and updates the countdown value.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} openingDate - The opening date of the market.
 * @param {string} openingTime - The opening time of the market.
 * @param {string} closingDate - The closing date of the market.
 * @param {string} closingTime - The closing time of the market.
 */
function updMarketCountdownLuxon(marketId, openingDate, openingTime, closingDate, closingTime) {
    var marketStatus = getMarketStatusVal(marketId);

    //Convert Date and Time strings to JS Date objects
    var openingDtString = openingDate + ' ' + openingTime;
    var openingDtJS = new Date(openingDtString);
    var closingDtString = closingDate + ' ' + closingTime;
    var closingDtJS = new Date(closingDtString);

    //Convert JS Date objects to Luxon DateTime objects with timezone
    var openingDtLuxon = luxon.DateTime.fromJSDate(openingDtJS, { zone: 'Europe/Athens' });
    var closingDtLuxon = luxon.DateTime.fromJSDate(closingDtJS, { zone: 'Europe/Athens' });

    var now_tz = luxon.DateTime.now().setZone("Europe/Athens");
    var diff = '00:00:00:00'

    if (now_tz > openingDtLuxon && now_tz < closingDtLuxon && (marketStatus === 'OPEN' || marketStatus === 'SUSPENDED')) {
        diff = luxon.Interval.fromDateTimes(now_tz, closingDtLuxon).toDuration(['days', 'hours', 'minutes', 'seconds']).toFormat('dd:hh:mm:ss');
    }
    else if (now_tz < openingDtLuxon && marketStatus != 'CLOSED') {
        diff = luxon.Interval.fromDateTimes(now_tz, openingDtLuxon).toDuration(['days', 'hours', 'minutes', 'seconds']).toFormat('dd:hh:mm:ss');
    }

    if (diff === '00:00:00:00' && ['PENDING', 'OPEN'].includes(marketStatus)) {
        marketSchedule();
        updMarketInstruments();
    }
    setCountDownVal(marketId, diff);
}


/**
 * Executes a trade for the specified market and instrument.
 *
 * Sends a trade request to the server and updates the DOM with the new positions and trade information.
 *
 * @param {string} marketId - The ID of the market.
 * @param {string} instrumentId - The ID of the instrument.
 * @param {string} [tradeType="BUY"] - The type of trade ("BUY" or "SELL").
 */
async function trade(marketId, instrumentId, tradeType = "BUY") {
    deactivateMarketTradeButtons(marketId);
    const shares = tradeType == "BUY" ? 1 : -1
    const response = await fetch(`${baseURL}/api/trades`, {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken')
        },
        method: 'POST',
        credentials: 'same-origin',
        body: JSON.stringify({
            instrument: instrumentId,
            type: tradeType,
            shares: shares
        })
    });
    //Trade went through, new positions returned. Update DOM.
    const tradePositions = await response.json();
    const positions = tradePositions.positions;
    const trade = tradePositions.trade;
    var tradeMarketId = trade.market_id;
    var cashPos = positions.Cash.size;

    for (pos in positions) {
        var position = positions[pos];
        if (pos == 'Cash') {
            setAvailFunds(tradeMarketId, position.size);
        }
        else {
            let payout = cashPos + position.size;
            setPositions(tradeMarketId, position.instrument.name, position.size);
            setPayout(position.instrument.id, payout);
        }
    }

    setUserTrades(tradeMarketId, tradePositions.n_exec_trades);
    updTradingBook(trade);
    await updMarketInstruments();
    let status = getMarketStatusVal(tradeMarketId);

    if (status === 'OPEN') {
        activateMarketTradeButtons(tradeMarketId);
    }
}


/**
 * Updates the trading book table with a new trade.
 *
 * Inserts a new row into the table with the details of the trade, including instrument name, action, quantity, price, timestamp, and status.
 *
 * @param {object} trade - The trade object containing the trade details.
 */
function updTradingBook(trade) {
    const tableId = 'trades_table_' + trade.market_id;
    var tsDate = new Date(trade.timestamp);
    var tableBody = document.getElementById(tableId);
    var row = tableBody.insertRow(0);
    const tradeData = [
        trade.instrument_name,
        trade.type,
        1,
        trade.price.toFixed(2),
        transformDatetime(tsDate),
        trade.status
    ];
    tradeData.forEach(data => {
        let cell = row.insertCell();
        cell.textContent = data;
    })
}


/**
 * Transforms a JavaScript Date object into a formatted date and time string.
 *
 * Uses the Intl.DateTimeFormat API to format the date and time according to the specified options.
 *
 * @param {Date} dateJS - The JavaScript Date object to be formatted.
 * @returns {string} The formatted date and time string.
 */
function transformDatetime(dateJS) {
    var formattedDate = new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(dateJS);
    formattedDate = formattedDate.replace("AM", "a.m.").replace("PM", "p.m.");
    formattedDate = formattedDate.replace(/([a-zA-Z]{3})\b/, '$1.');

    return formattedDate;
}


/**
 * Updates the AUM (Assets Under Management) and PNL (Profit and Loss) for a given market.
 *
 * Calculates the AUM based on cash position, yes/no positions, and yes/no prices.
 * Then updates the AUM, PNL, and starting funds elements in the DOM.
 *
 * @param {string} marketId - The ID of the market.
 */
function updateAUM(marketId) {
    const marketNode = document.getElementById(marketId + '_market');
    const cashPos = parseFloat(marketNode.querySelector("[cash_pos]").textContent);
    const yesPos = parseFloat(marketNode.querySelector("[yes_pos]").textContent);
    const noPos = parseFloat(marketNode.querySelector("[no_pos]").textContent);
    const yesPrice = parseFloat(marketNode.querySelector("[yes_price]").textContent);
    const noPrice = parseFloat(marketNode.querySelector("[no_price]").textContent);
    const aum = cashPos + (yesPos * yesPrice) + (noPos * noPrice);
    const aumEl = document.getElementById(marketId + '_aum');
    const pnlEl = document.getElementById(marketId + '_pnl');
    const sfEl = document.getElementById(marketId + '_sf');
    const pnl = aum - parseFloat(sfEl.textContent);
    aumEl.innerHTML = aum.toFixed(2);
    pnlEl.innerHTML = pnl.toFixed(2);
}


/**
 * Shows the trades modal for a given market.
 *
 * Sets the visibility and width of the trades modal element to make it visible on the screen.
 *
 * @param {string} marketId - The ID of the market.
 */
function showTrades(marketId) {
    const tradesModalId = marketId + "_trading_book"
    const tradesModalEl = document.getElementById(tradesModalId)
    tradesModalEl.style.visibility = 'visible';
    tradesModalEl.style.width = '100vw';
}


/**
 * Hides the trades modal for a given market.
 *
 * Sets the visibility and width of the trades modal element to hide it from the screen.
 *
 * @param {string} marketId - The ID of the market.
 */
function hideTrades(marketId) {
    const tradesModalId = marketId + "_trading_book"
    const tradesModalEl = document.getElementById(tradesModalId)
    tradesModalEl.style.visibility = 'hidden';
    tradesModalEl.style.width = '00vw';
}


/**
 * Toggles the visibility of market details.
 *
 * @param {string} marketId - The ID of the market.
 */
function toggleMarketDetails(marketId) {
    const marketDetailsId = marketId + "_details"
    const marketDetailsEl = document.getElementById(marketDetailsId)
    const marketDetailsLabelId = marketId + "_details_label"
    const marketDetailsLabelEl = document.getElementById(marketDetailsLabelId)
    const style = getComputedStyle(marketDetailsEl);
    if(style.maxHeight === '0px'){
        marketDetailsEl.style.maxHeight = '50em';
        setTimeout(()=>{
            marketDetailsLabelEl.textContent = 'Hide Details';
        },300);
    }
    else{
        marketDetailsEl.style.maxHeight = '0px';
        setTimeout(()=>{
            marketDetailsLabelEl.textContent = 'Show Details';
        },300);
    }
}


/**
 * Fetches the market schedule from the server.
 */
async function marketSchedule() {
    const schedule = await fetch(`${baseURL}/api/schedule`);
}


/**
 * Updates market instrument prices every 2 seconds.
 */
function setUpdatePricesRepeat() {
    const priceUpdate = setInterval(() => updMarketInstruments(), 2000);
}


/**
 * Sets up sliding animation for market names that are wider than their containers.
 *
 */
function setSlidingMarketNames(){
	const allMarketTitles = document.querySelectorAll("div.market-header-title");
	allMarketTitles.forEach((c)=>{
		var title_text = c.querySelector("span");
		if (c.clientWidth < title_text.clientWidth){
			title_text.classList.add("animate-market-title");
		}
	});
}