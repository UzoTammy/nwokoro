"""
Static content for the "Learn" investment tutorial section. Kept as plain
Python data (no model/migration) since it's editorial content, not user data.
"""

INVESTMENT_TUTORIALS = [
    {
        'slug': 'stocks',
        'title': 'Stocks (Equities)',
        'icon': 'fa-chart-line',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Buying a share of ownership in a public company, betting on its future earnings and growth.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-building', 'label': 'Public Company'},
            {'icon': 'fa-hand-holding-usd', 'label': 'Dividends & Price Growth'},
        ],
        'content': [
            "A stock represents a slice of ownership in a company. When you buy shares, you become a "
            "part-owner and your return comes from two places: price appreciation (the share becoming "
            "worth more) and dividends (a portion of profit paid out to shareholders).",
            "Stocks are traded on public exchanges, so prices move constantly based on company "
            "performance, interest rates, and overall market sentiment. That liquidity is a strength — "
            "you can usually buy or sell within seconds — but it also means short-term prices can swing "
            "sharply even when nothing about the underlying business has changed.",
            "Over long time horizons, equities have historically outpaced inflation and most other asset "
            "classes, which is why they're a core holding in most portfolios. The tradeoff is volatility: "
            "a stock can lose a large share of its value in a downturn, and there's no guarantee it "
            "recovers on any particular timeline.",
        ],
        'key_points': [
            "Ownership stake — returns come from price growth and dividends.",
            "Highly liquid: easy to buy and sell on public exchanges.",
            "Volatile in the short term; historically strong over long horizons.",
            "Diversifying across many companies/sectors reduces single-company risk.",
        ],
    },
    {
        'slug': 'bonds',
        'title': 'Bonds (Fixed Income)',
        'icon': 'fa-file-invoice-dollar',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'Lending money to a government or company in exchange for regular interest payments.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-landmark', 'label': 'Government / Corporation'},
            {'icon': 'fa-coins', 'label': 'Interest + Principal'},
        ],
        'content': [
            "A bond is essentially a loan. You give an issuer — a government or a corporation — a fixed "
            "sum, and in return they pay you periodic interest (the 'coupon') and return your principal "
            "at a set maturity date.",
            "Bonds are generally less volatile than stocks because the payment schedule is contractual, "
            "not dependent on how well the business performs. Government bonds from stable countries are "
            "considered among the safest investments available; corporate bonds pay more but carry more "
            "risk that the issuer could default.",
            "The main risks are interest-rate risk (bond prices fall when rates rise, if you need to sell "
            "before maturity) and credit risk (the issuer failing to pay). Inflation is also a quiet risk: "
            "a fixed coupon buys less over time if prices are rising quickly.",
        ],
        'key_points': [
            "A loan you make to a government or company for regular interest.",
            "Lower volatility than stocks; used to balance a portfolio.",
            "Price moves inversely with interest rates if sold before maturity.",
            "Higher-yield ('junk') bonds trade extra return for extra default risk.",
        ],
    },
    {
        'slug': 'mutual-funds-etfs',
        'title': 'Mutual Funds & ETFs',
        'icon': 'fa-layer-group',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Pooled baskets of stocks, bonds, or other assets that give instant diversification in one purchase.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-layer-group', 'label': 'Pooled Fund'},
            {'icon': 'fa-th', 'label': 'Many Underlying Assets'},
        ],
        'content': [
            "Mutual funds and ETFs (exchange-traded funds) both pool money from many investors to buy a "
            "diversified basket of underlying assets — often hundreds of stocks or bonds at once. Instead "
            "of picking individual securities, you buy a single unit that represents a slice of the whole "
            "basket.",
            "The practical difference is how they trade: mutual funds are priced and settled once a day "
            "after markets close, while ETFs trade continuously on an exchange like a stock, so their "
            "price can move throughout the day. ETFs also tend to have lower fees, especially index-tracking ones.",
            "Because a single fund can span an entire market or sector, funds are one of the easiest ways "
            "to diversify without needing to research dozens of individual companies yourself. The cost is "
            "the management fee (expense ratio), which eats into returns over time — even small differences "
            "compound significantly over decades.",
        ],
        'key_points': [
            "One purchase buys exposure to many underlying securities at once.",
            "ETFs trade all day like stocks; mutual funds price once daily.",
            "Index funds/ETFs usually have the lowest fees and match market returns.",
            "Actively managed funds charge more, aiming to beat the market — most don't, consistently.",
        ],
    },
    {
        'slug': 'real-estate',
        'title': 'Real Estate',
        'icon': 'fa-home',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Owning physical property directly, earning through rental income and long-term appreciation.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-home', 'label': 'Property'},
            {'icon': 'fa-hand-holding-usd', 'label': 'Rent & Appreciation'},
        ],
        'content': [
            "Real estate investing means owning physical property — residential, commercial, or land — "
            "with the goal of generating rental income, capital appreciation, or both. Unlike stocks and "
            "bonds, it's a tangible, illiquid asset: selling can take weeks or months, not seconds.",
            "Rental property can produce steady cash flow, and mortgage leverage lets you control an asset "
            "worth far more than your initial cash outlay — amplifying both gains and losses. Property "
            "values also tend to move differently from financial markets, which can smooth out a "
            "portfolio's overall swings.",
            "The downsides are real: maintenance costs, vacancy periods, property taxes, and the effort of "
            "managing tenants (or paying someone to). Real estate is also concentrated risk — your money "
            "is tied to the fortunes of one property in one location, rather than spread across a market.",
        ],
        'key_points': [
            "Tangible asset generating rental income and/or appreciation.",
            "Illiquid — takes real time and cost to buy or sell.",
            "Leverage (mortgages) can amplify both returns and losses.",
            "Concentrated in a single property/location, unlike a diversified fund.",
        ],
    },
    {
        'slug': 'business-equity',
        'title': 'Business Equity',
        'icon': 'fa-briefcase',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Owning a stake in a private business — your own or someone else’s — outside the public markets.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-briefcase', 'label': 'Private Business'},
            {'icon': 'fa-chart-line', 'label': 'Profit Share & Exit Value'},
        ],
        'content': [
            "Business equity is ownership in a company that isn't publicly traded — your own venture, a "
            "family business, or a stake bought privately. Returns come from the business's profits "
            "(distributions or reinvested growth) and, eventually, from selling the stake or the business "
            "itself.",
            "Because there's no public market setting a daily price, valuing private equity is more art "
            "than science, and it's far less liquid than stocks — there may be no ready buyer when you "
            "want to exit. Recapitalizing or growing the business (plowing profits back in) directly "
            "affects your equity value in a way that's much more hands-on than owning a public stock.",
            "This is typically the highest-risk, highest-control asset class: you (or the owner you're "
            "investing alongside) can directly influence outcomes through decisions, but a struggling "
            "business can also lose most or all of its value with no market floor to catch it.",
        ],
        'key_points': [
            "Ownership in a private company, not traded on an exchange.",
            "Illiquid — no guaranteed buyer if you want to sell your stake.",
            "Value tied directly to the business's operating performance.",
            "Highest potential control and upside, but concentrated risk.",
        ],
    },
    {
        'slug': 'fixed-term-deposits',
        'title': 'Fixed / Term Deposits',
        'icon': 'fa-piggy-bank',
        'risk': 'Very Low',
        'risk_class': 'very-low',
        'summary': 'Locking savings with a bank for a set period in exchange for a guaranteed interest rate.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-piggy-bank', 'label': 'Bank (Locked Term)'},
            {'icon': 'fa-coins', 'label': 'Guaranteed Interest'},
        ],
        'content': [
            "A fixed or term deposit (also called a GIC or CD depending on the country) is money placed "
            "with a bank for a set period — say 3, 6, or 12 months — in exchange for a guaranteed interest "
            "rate, usually higher than a regular savings account.",
            "The appeal is certainty: you know exactly what you'll earn, and in most countries deposits up "
            "to a certain amount are government-insured, making this one of the safest ways to hold money. "
            "The tradeoff is that your money is locked up — withdrawing early usually means a penalty or "
            "losing the promised rate.",
            "Because the return is fixed and modest, term deposits rarely outpace inflation by much, if at "
            "all. They're best used for money you'll need with certainty within a known timeframe — an "
            "emergency fund or a near-term goal — rather than as a long-term growth vehicle.",
        ],
        'key_points': [
            "Guaranteed interest rate for locking funds over a fixed term.",
            "Very low risk; often government-insured up to a limit.",
            "Early withdrawal usually forfeits some or all of the interest.",
            "Best for short-term savings, not long-term wealth growth.",
        ],
    },
    {
        'slug': 'cryptocurrency',
        'title': 'Cryptocurrency',
        'icon': 'fa-coins',
        'risk': 'Very High',
        'risk_class': 'very-high',
        'summary': 'Digital assets built on blockchain networks, trading 24/7 with no central issuer.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-link', 'label': 'Blockchain Network'},
            {'icon': 'fa-chart-line', 'label': 'Market Price (24/7)'},
        ],
        'content': [
            "Cryptocurrencies are digital assets that exist on decentralized blockchain networks rather "
            "than being issued by a government or company. Bitcoin and Ethereum are the largest by market "
            "value, but thousands of others exist with wildly different purposes and credibility.",
            "Unlike stock markets, crypto markets trade 24 hours a day, seven days a week, with no circuit "
            "breakers. Prices are driven heavily by sentiment, adoption news, and speculation rather than "
            "earnings or cash flow — there's often no underlying business generating profit to anchor a "
            "valuation.",
            "This makes crypto the most volatile major asset class: it's realistic to see 20%+ price "
            "swings in a single day. Custody is also a real risk of its own — losing access to a private "
            "key or trusting an insolvent exchange can mean losing funds entirely, with none of the "
            "protections that apply to regulated banks or brokerages.",
        ],
        'key_points': [
            "Decentralized digital assets with no earnings/cash flow to anchor value.",
            "Trades continuously; extremely volatile compared to stocks or bonds.",
            "Value driven largely by sentiment, adoption, and speculation.",
            "Self-custody and exchange risk are unique to this asset class.",
        ],
    },
    {
        'slug': 'money-market',
        'title': 'Money Market Instruments',
        'icon': 'fa-university',
        'risk': 'Very Low',
        'risk_class': 'very-low',
        'summary': 'Ultra-short-term, highly liquid debt used to safely park cash while it still earns something.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-university', 'label': 'Short-Term Debt Pool'},
            {'icon': 'fa-tachometer-alt', 'label': 'Quick Liquidity'},
        ],
        'content': [
            "Money market instruments are short-term debt — typically maturing in a year or less — issued "
            "by governments, banks, or highly-rated corporations. Treasury bills and money market funds are "
            "the most common ways individuals access this asset class.",
            "The goal isn't growth, it's capital preservation with modest, stable income while keeping the "
            "money accessible. Money market funds are designed to hold their value (often targeting a "
            "stable unit price) and can typically be withdrawn quickly, making them a common place to "
            "park cash between other investments.",
            "Because maturities are so short and issuers are typically high-credit-quality, the risk of "
            "loss is very low — but so is the return, which usually tracks close to prevailing short-term "
            "interest rates and rarely beats inflation by much over time.",
        ],
        'key_points': [
            "Short-term, high-quality debt instruments (e.g. treasury bills).",
            "Prioritizes safety and liquidity over growth.",
            "Common place to park cash between other investments.",
            "Returns track short-term interest rates — modest, not a growth engine.",
        ],
    },
    {
        'slug': 'commercial-paper',
        'title': 'Commercial Paper',
        'icon': 'fa-file-signature',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'Short-term, unsecured IOUs that large corporations issue to cover near-term cash needs.',
        'diagram': [
            {'icon': 'fa-building', 'label': 'Corporation'},
            {'icon': 'fa-file-signature', 'label': 'Discounted IOU'},
            {'icon': 'fa-user', 'label': 'You (buy at a discount)'},
        ],
        'content': [
            "Commercial paper is short-term, unsecured debt that large, creditworthy corporations issue to "
            "fund immediate needs — payroll, inventory, receivables — rather than borrowing from a bank. "
            "It's sold at a discount to face value and matures anywhere from a few days up to 270 days, "
            "with the return coming from the difference between what you pay and what you're repaid.",
            "Because there's no collateral backing it, commercial paper relies entirely on the issuing "
            "company's credit standing — only well-established, financially strong corporations can issue "
            "it economically. Credit rating agencies grade issuers, and lower-rated paper has to offer a "
            "higher yield to attract buyers.",
            "It sits close to money market instruments and treasury bills on the risk spectrum: short "
            "maturities keep interest-rate exposure low, but unlike government-issued paper, there's real "
            "default risk if the issuing company runs into trouble — a risk that briefly caused real "
            "market stress during the 2008 financial crisis when investors lost confidence in some issuers.",
        ],
        'key_points': [
            "Unsecured short-term debt issued by large corporations (up to ~270 days).",
            "Sold at a discount; the discount-to-face-value gap is your return.",
            "No collateral — return depends entirely on the issuer's creditworthiness.",
            "Lower rate risk than long bonds, but real default risk unlike government paper.",
        ],
    },
]


def get_tutorial(slug):
    return next((t for t in INVESTMENT_TUTORIALS if t['slug'] == slug), None)
