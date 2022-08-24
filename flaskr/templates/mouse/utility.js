// ================================================================== //
// Data samples
// ================================================================== //
var balance = 2000;
var averageExpensePerCategory = { "Rent": -750, "Food": -1056, "Cosmetics": -1600, "Activities": -500, "Mobility": -1950, "Books": -2100};
var FinancialData = [
    {'date': new Date('01/02/2020'), 'product': 'Flat', 'product category': 'Rent', 'amount': -350, 'payment method': 'Bank transfer'},
    {'date': new Date('01/09/2020'), 'product': 'Salary', 'product category': 'Salary', 'amount': 174, 'payment method': 'Check'},
    {'date': new Date('01/09/2020'), 'product': 'Bread', 'product category': 'Food', 'amount': -130, 'payment method': 'PayPal'},
    {'date': new Date('01/06/2020'), 'product': 'Shampoo', 'product category': 'Cosmetics', 'amount': -119, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -160, 'payment method': 'Credit Card'},
    {'date': new Date('01/01/2020'), 'product': 'Razor', 'product category': 'Cosmetics', 'amount': -48, 'payment method': 'Cash'},
    {'date': new Date('01/09/2020'), 'product': 'Cinema', 'product category': 'Activities', 'amount': -25, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Book - How to become a Web Developer', 'product category': 'Books', 'amount': -350, 'payment method': 'Cash'},
    {'date': new Date('01/01/2020'), 'product': 'Salary', 'product category': 'Salary', 'amount': 400, 'payment method': 'Cash'},
    {'date': new Date('01/10/2020'), 'produc    t': 'Apple', 'product category': 'Stock Market', 'amount': 176, 'payment method': 'PayPal'},
    {'date': new Date('01/04/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 66, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Car Insurance', 'product category': 'Mobility', 'amount': -175, 'payment method': 'Check'},
    {'date': new Date('01/05/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 120, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/05/2020'), 'product': 'Harry Potter', 'product category': 'Books', 'amount': -188, 'payment method': 'Credit Card'},
    {'date': new Date('01/09/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -75, 'payment method': 'Bank transfer'},
    {'date': new Date('01/05/2020'), 'product': 'Restaurant', 'product category': 'Food', 'amount': -120, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/03/2020'), 'product': 'Product A', 'product category': 'Sells ebay', 'amount': 5, 'payment method': 'Credit Card'},
    {'date': new Date('01/03/2020'), 'product': 'BMW', 'product category': 'Stock Market', 'amount': 311, 'payment method': 'PayPal'},
    {'date': new Date('01/09/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 185, 'payment method': 'Bank transfer'},
    {'date': new Date('01/04/2020'), 'product': 'Creme', 'product category': 'Cosmetics', 'amount': -120, 'payment method': 'Credit Card'},
    {'date': new Date('01/08/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 60, 'payment method': 'Bank transfer'},
    {'date': new Date('01/09/2020'), 'product': 'Party', 'product category': 'Activities', 'amount': -220, 'payment method': 'PayPal'},
    {'date': new Date('01/08/2020'), 'product': 'Product B', 'product category': 'Sells ebay', 'amount': 290, 'payment method': 'Credit Card'},
    {'date': new Date('01/01/2020'), 'product': 'Car Renatl', 'product category': 'Mobility', 'amount': -317, 'payment method': 'Bank transfer'},
    {'date': new Date('01/02/2020'), 'product': 'Tesla', 'product category': 'Stock Market', 'amount': 280, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 46, 'payment method': 'PayPal'},
    {'date': new Date('01/03/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 253, 'payment method': 'Check'},
    {'date': new Date('01/01/2020'), 'product': 'How to become a Web Developer', 'product category': 'Books', 'amount': -35, 'payment method': 'Credit Card'},
    {'date': new Date('01/04/2020'), 'product': 'Product C', 'product category': 'Sells ebay', 'amount': 30, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/04/2020'), 'product': 'Facebook', 'product category': 'Stock Market', 'amount': 204, 'payment method': 'Credit Card'},
    {'date': new Date('01/03/2020'), 'product': 'The Neverending Story', 'product category': 'Books', 'amount': -231, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -336, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Tooth brush', 'product category': 'Cosmetics', 'amount': -70, 'payment method': 'Bank transfer'},
    {'date': new Date('01/10/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 108, 'payment method': 'Cash'},
    {'date': new Date('01/04/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 132, 'payment method': 'Cash'},
    {'date': new Date('01/04/2020'), 'product': 'Soccer', 'product category': 'Activities', 'amount': -248, 'payment method': 'Cash'},
    {'date': new Date('01/05/2020'), 'product': 'Public transport', 'product category': 'Mobility', 'amount': -240, 'payment method': 'PayPal'},
    {'date': new Date('01/08/2020'), 'product': 'Faust', 'product category': 'Books', 'amount': -178, 'payment method': 'Credit Card'},
    {'date': new Date('01/05/2020'), 'product': 'Product D', 'product category': 'Sells ebay', 'amount': 260, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Italian restaurant', 'product category': 'Food', 'amount': -270, 'payment method': 'PayPal'},
    {'date': new Date('01/02/2020'), 'product': 'Restaurant', 'product category': 'Food', 'amount': -381, 'payment method': 'PayPal'},
    {'date': new Date('01/01/2020'), 'product': 'cosmetic treatment', 'product category': 'Cosmetics', 'amount': -201, 'payment method': 'PayPal'},
    {'date': new Date('01/09/2020'), 'product': 'Theater', 'product category': 'Activities', 'amount': -108, 'payment method': 'Cash'},
    {'date': new Date('01/06/2020'), 'product': 'E-Bike', 'product category': 'Mobility', 'amount': -242, 'payment method': 'Check'},
    {'date': new Date('01/09/2020'), 'product': 'The Lean Startup', 'product category': 'Books', 'amount': -121, 'payment method': 'Bank transfer'},
    {'date': new Date('01/07/2020'), 'product': 'WireCard', 'product category': 'Stock Market', 'amount': 6, 'payment method': 'PayPal'},
    {'date': new Date('01/03/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 41, 'payment method': 'Cash'},
    {'date': new Date('01/09/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 284, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Computer Games', 'product category': 'Activities', 'amount': -246, 'payment method': 'Cash'},
    {'date': new Date('01/08/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -332, 'payment method': 'Cash'},
    {'date': new Date('01/01/2020'), 'product': 'Cosmetic treatment', 'product category': 'Cosmetics', 'amount': -99, 'payment method': 'Credit Card'},
    {'date': new Date('01/08/2020'), 'product': 'Product E', 'product category': 'Sells ebay', 'amount': 311, 'payment method': 'Credit Card'},
    {'date': new Date('01/01/2020'), 'product': 'Alibaba', 'product category': 'Stock Market', 'amount': 198, 'payment method': 'Credit Card'},
    {'date': new Date('01/05/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 188, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/07/2020'), 'product': 'Bars', 'product category': 'Activities', 'amount': -189, 'payment method': 'Credit Card'},
    {'date': new Date('01/08/2020'), 'product': 'Gas', 'product category': 'Mobility', 'amount': -378, 'payment method': 'PayPal'},
    {'date': new Date('01/02/2020'), 'product': 'The Little Prince', 'product category': 'Books', 'amount': -205, 'payment method': 'Check'},
    {'date': new Date('01/02/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 136, 'payment method': 'Check'},
    {'date': new Date('01/05/2020'), 'product': 'Taxi', 'product category': 'Mobility', 'amount': -397, 'payment method': 'Check'},
    {'date': new Date('01/04/2020'), 'product': 'Product F', 'product category': 'Sells ebay', 'amount': 96, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -47, 'payment method': 'Bank transfer'},
    {'date': new Date('01/07/2020'), 'product': 'ALM', 'product category': 'Stock Market', 'amount': 101, 'payment method': 'Bank transfer'},
    {'date': new Date('01/06/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 382, 'payment method': 'Bank transfer'},
    {'date': new Date('01/04/2020'), 'product': 'Lipgloss', 'product category': 'Cosmetics', 'amount': -17, 'payment method': 'PayPal'},
    {'date': new Date('01/10/2020'), 'product': 'Hiking', 'product category': 'Activities', 'amount': -25, 'payment method': 'Check'},
    {'date': new Date('01/06/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 242, 'payment method': 'Check'},
    {'date': new Date('01/02/2020'), 'product': 'Gas', 'product category': 'Mobility', 'amount': -346, 'payment method': 'Check'},
    {'date': new Date('01/06/2020'), 'product': 'Feynman lectures', 'product category': 'Books', 'amount': -344, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/03/2020'), 'product': 'Product G', 'product category': 'Sells ebay', 'amount': 398, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/10/2020'), 'product': 'Restaurant', 'product category': 'Rent', 'amount': -379, 'payment method': 'PayPal'},
    {'date': new Date('01/07/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -382, 'payment method': 'PayPal'},
    {'date': new Date('01/01/2020'), 'product': 'Ford', 'product category': 'Stock Market', 'amount': 21, 'payment method': 'PayPal'},
    {'date': new Date('01/06/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 352, 'payment method': 'Check'},
    {'date': new Date('01/08/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 358, 'payment method': 'PayPal'},
    {'date': new Date('01/08/2020'), 'product': 'Product H', 'product category': 'Sells ebay', 'amount': 180, 'payment method': 'Credit Card'},
    {'date': new Date('01/01/2020'), 'product': 'Parfum', 'product category': 'Cosmetics', 'amount': -396, 'payment method': 'PayPal'},
    {'date': new Date('01/03/2020'), 'product': 'Amusement park', 'product category': 'Activities', 'amount': -247, 'payment method': 'PayPal'},
    {'date': new Date('01/01/2020'), 'product': 'Train', 'product category': 'Mobility', 'amount': -189, 'payment method': 'Bank transfer'},
    {'date': new Date('01/08/2020'), 'product': 'PayPal', 'product category': 'Stock Market', 'amount': 246, 'payment method': 'Cash'},
    {'date': new Date('01/03/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 374, 'payment method': 'Credit Card'},
    {'date': new Date('01/06/2020'), 'product': 'A Christmas Carol', 'product category': 'Books', 'amount': -323, 'payment method': 'Check'},
    {'date': new Date('01/02/2020'), 'product': 'Ice cream in the park', 'product category': 'Activities', 'amount': -157, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/09/2020'), 'product': 'Grocery Store', 'product category': 'Food', 'amount': -20, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/05/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 326, 'payment method': 'Credit Card'},
    {'date': new Date('01/06/2020'), 'product': 'Product I', 'product category': 'Sells ebay', 'amount': 106, 'payment method': 'Check'},
    {'date': new Date('01/05/2020'), 'product': 'Shampoo', 'product category': 'Cosmetics', 'amount': -32, 'payment method': 'PayPal'},
    {'date': new Date('01/08/2020'), 'product': 'Daimler', 'product category': 'Stock Market', 'amount': 90, 'payment method': 'Bank transfer'},
    {'date': new Date('01/09/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 15, 'payment method': 'Check'},
    {'date': new Date('01/08/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 28, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Swimming', 'product category': 'Activities', 'amount': -162, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/06/2020'), 'product': 'Product J', 'product category': 'Sells ebay', 'amount': 29, 'payment method': 'Bank transfer'},
    {'date': new Date('01/09/2020'), 'product': 'Alphabet', 'product category': 'Stock Market', 'amount': 394, 'payment method': 'Check'},
    {'date': new Date('01/08/2020'), 'product': 'Savings', 'product category': 'Interest', 'amount': 262, 'payment method': 'Mobile Payment'},
    {'date': new Date('01/05/2020'), 'product': 'Car Insurance', 'product category': 'Mobility', 'amount': -127, 'payment method': 'Credit Card'},
    {'date': new Date('01/10/2020'), 'product': 'Flat', 'product category': 'Rental Income', 'amount': 389, 'payment method': 'Credit Card'},
    {'date': new Date('01/07/2020'), 'product': 'Product K', 'product category': 'Sells ebay', 'amount': 94, 'payment method': 'PayPal'}
];

// ================================================================== //
// General styling variables 
// ================================================================== //
var bgC = {'red': "rgba(255, 99, 132, 0.7)", 'orange': "rgba(255, 159, 64, 0.7)", 'yellow': "rgba(255, 205, 86, 0.7)", 'green': "rgba(75, 192, 192, 0.7)", 'blue': "rgba(54, 162, 235,0.7)", 'violett': "rgba(153, 102, 255, 0.7)", 'grey': "rgba(201, 203, 207, 0.7)"};
var backgroundColorCategory = [bgC.red, bgC.orange, bgC.yellow, bgC.green, bgC.blue, bgC.violett, bgC.grey];
var cssColors =     {'first-bg-color':  '#1B161F', 'second-bg-color': '#1B2533;', 'first-font-color': 'white','second-font-color': '#21cd92'};

// ================================================================== //
// Helper functions 
// ================================================================== //
function groupByDate(array) {
    var result = [];
    array.reduce(function (res, value) {
        if (!res[value.date]) {
            res[value.date] = { x: new Date(value.date), y: 0 };
            result.push(res[value.date]);
        }
        res[value.date].y += value.amount;
        return res;
    }, {});
    return result;
}

function groupByCategory(array) {
    var result = [];
    array.reduce(function (res, value) {
        if (!res[value['product category']]) {
            res[value['product category']] = { x: value['product category'], y: 0 };
            result.push(res[value['product category']]);
        }
        res[value['product category']].y += value.amount;
        return res;
    }, {});
    return result;
}

function groupByPaymentMethod(array) {
    var result = [];
    array.reduce(function (res, value) {
        if (!res[value['payment method']]) {
            res[value['payment method']] = { x: value['payment method'], y: 0 };
            result.push(res[value['payment method']]);
        }
        res[value['payment method']].y += value.amount;
        return res;
    }, {});
    return result;
}

function compare(a, b) {
    if (a.x < b.x) return -1;
    if (a.x > b.x) return 1;
    return 0;
}

function accumulate(array) {
    return array.map(function (val) { return { x: val.x, y: this.acc += val.y }; }, { acc: balance });
}

// ================================================================== //
// Data manipulation
// ================================================================== //

// Split data for income and expenses
var income = FinancialData.filter(function (entry) { return entry.amount >= 0; });
var cost = FinancialData.filter(function (entry) { return entry.amount < 0; });

// Calculate overal totals, splitted for income and expenses, to determine relative weights
var incomeTotals = income.reduce(function (val, data) { return val + data.amount; }, 0);
var costTotals = cost.reduce(function (val, data) { return val + data.amount; }, 0);

// Group various data (splitted for income and expenses) by 
//  -- date
var costGroupedByDate = groupByDate(cost).sort(compare);
var incomeGroupedByDate = groupByDate(income).sort(compare);

//  -- category
var incomeGroupedByCategory = { category: groupByCategory(income).map(a => a.x), amount: groupByCategory(income).map(a => a.y) };
var costGroupedByCategory = { category: groupByCategory(cost).map(a => a.x), amount: groupByCategory(cost).map(a => a.y) };

// ========== Enahnce data with benchmark figures (splitted for income and expenses)
var costGroupedByCategoryBenchmark = [];
groupByCategory(cost).forEach((elem, i) => {
    costGroupedByCategoryBenchmark.push({
        label: elem.x, backgroundColor: backgroundColorCategory[i], data: [{
            x: elem.y,
            y: averageExpensePerCategory[elem.x],
            r: elem.y / costTotals * 100
        }]
    });
});

var incomeGroupedByCategoryBenchmark = [];
groupByCategory(income).forEach(elem => {
    incomeGroupedByCategoryBenchmark.push({
        label: elem.x, backgroundColor: 'red', borderColor: 'red', borderWidth: 1, data: [{
            x: elem.y,
            y: averageExpensePerCategory[elem.x],
            r: elem.y / incomeTotals * 100
        }]
    });
});

//  -- payment methos
var incomeGroupedByPaymentMethod = { category: groupByPaymentMethod(income).map(a => a.x), amount: groupByPaymentMethod(income).map(a => a.y / incomeTotals * 100) };
var costGroupedByPaymentMethod = { category: groupByPaymentMethod(cost).map(a => a.x), amount: groupByPaymentMethod(cost).map(a => a.y / costTotals * 100) };

// Group AND accumulate by 
//  -- date
var totalsGroupedByDate = groupByDate(FinancialData).sort(compare);
var totalsAccGroupedByDate = accumulate(totalsGroupedByDate);