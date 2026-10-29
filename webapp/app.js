"use strict";

const telegram = window.Telegram && window.Telegram.WebApp;
if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor("#090b0d");
  telegram.setBackgroundColor("#090b0d");
}

const translations = {
  ru: {
    locale: "ru-RU", pageTitle: "SavvyApp — найди лучший вариант", homeAria: "SAVVY — главная", promisesAria: "Что SAVVY проверяет", beta: "AI SHOPPING INTELLIGENCE", heroEyebrow: "PURCHASE INTELLIGENCE", heroTitle: "Проверь перед покупкой.",
    heroDescription: "Название или ссылка на товар — SAVVY проверит совпадение, цену и условия доставки.", sectionEyebrow: "ЧТО ВЫ ХОТИТЕ ПРОВЕРИТЬ?",
    formTitle: "Добавьте товар или ссылку", productName: "Что хотите проверить или найти?", modeText: "✎ Текст", modeLink: "↗ Ссылка на товар", placeholder: "Например, футболка Nike до 100 BYN", linkPlaceholder: "Вставьте публичную ссылку на страницу товара", paste: "Вставить",
    fieldHint: "Напишите название, характеристики и бюджет или вставьте ссылку на товар.", shipTo: "Доставка", displayCurrency: "Валюта", searchButton: "Проверить предложение",
    searching: "Ищем лучший вариант…", searchingHint: "Сравниваем совпадения, цены и известные расходы. Это может занять до минуты.", conversationHint: "Привет! Напиши, какой товар или подарок ищешь, и укажи бюджет — я помогу сравнить предложения.",
    trustNote: "Часть площадок работает нестабильно. Доставка и пошлины могут быть оценочными; курсы валют пока ориентировочные — итог перепроверь у продавца.",
    privacyNote: "Название и выбранная страна отправляются Telegram-боту и поисковым площадкам. Mini App не сохраняет их в базе.",
    resultsEyebrow: "РЕЗУЛЬТАТ ПОИСКА", resultsTitle: "Лучший вариант", newSearch: "Новый поиск", promiseCost: "Итоговая стоимость",
    promiseSeller: "Надёжность продавца", promiseMatch: "Совпадение товара", footerSlogan: "Покупай осознанно.",
    exact: "Точное совпадение", similar: "Похожий товар", giftIdea: "Идея подарка", productPrice: "Цена товара", totalPrice: "Итого с расходами", estimatedTotal: "Оценка итого*",
    seller: "Продавец", shipsFrom: "Отправка", risk: "Риск", dealQuality: "Оценка качества сделки", why: "Почему SAVVY выбрал этот вариант", matched: "Совпали характеристики: ",
    matchExactReason: "Совпадение товара подтверждено по найденным характеристикам.", matchSimilarReason: "Это близкий вариант: полное совпадение подтвердить не удалось.",
    lowestTotal: "Минимальная подтверждённая полная стоимость среди найденных совпадений.", lowestPrice: "Минимальная цена товара среди найденных совпадений; доставка могла быть не учтена.",
    qualityTie: "При одинаковой цене у предложения лучше оценка качества по доступным данным.", riskTie: "При одинаковой стоимости у предложения ниже расчётный риск.", onlyComparable: "Других сравнимых предложений с ценой не найдено.",
    details: "Расходы и условия", hideDetails: "Скрыть подробности", delivery: "Доставка", taxes: "Налоги", duties: "Пошлина", unconfirmed: "не подтверждена", estimated: " · оценка",
    knownTotalNote: "Сумма рассчитана по известным компонентам.", unknownTotalNote: "Полная стоимость не подтверждена. Проверь сумму на странице продавца.",
    openProduct: "Открыть товар", compare: "Сравнить другие варианты", hideCompare: "Скрыть сравнение", found: "Найдено вариантов", noOffers: "Надёжных предложений с ценой пока нет.",
    refineSearch: "Попробуй добавить бренд, модель, размер или другую важную деталь.", noPrice: "Цена не указана", pasteUnavailable: "Буфер обмена недоступен. Вставь текст в поле вручную.",
    pasteFailed: "Не удалось прочитать буфер обмена. Вставь текст вручную.", clipboardEmpty: "Буфер обмена пуст.", tooShort: "Напиши название товара — хотя бы два символа.",
    linksUnsupported: "Вставь публичную ссылку на страницу товара с http:// или https://.", openTelegram: "Открой приложение кнопкой ✨ SavvyApp в сообщении бота или в меню чата.",
    helpTitle: "Помощь по приложению", helpBody: "Введите название товара или переключитесь на ссылку. Укажите страну доставки и валюту. SAVVY покажет точные совпадения и известные расходы; если продавец не подтвердил доставку или пошлину, сумма будет помечена отдельно.", helpLimits: "Фото, история цен и автоматические уведомления пока не подключены.",
    noAlternatives: "Других вариантов пока нет", searchError: "Не удалось выполнить поиск. Попробуй ещё раз.", rateLimited: "Слишком много запросов. Попробуй через минуту.", invalidSearch: "Проверь название товара и страну доставки.",
    regionNames: { BY: "Беларусь", RU: "Россия", KZ: "Казахстан", UZ: "Узбекистан", KG: "Кыргызстан", AM: "Армения", AZ: "Азербайджан", MD: "Молдова", TJ: "Таджикистан", TM: "Туркменистан", GE: "Грузия", UA: "Украина" },
    attributes: { brand: "бренд", model: "модель", color: "цвет", size: "размер", storage: "память", material: "материал", category: "категория", condition: "состояние" },
  },
  en: {
    locale: "en-US", pageTitle: "SavvyApp — find the best option", homeAria: "SAVVY — home", promisesAria: "What SAVVY checks", beta: "AI SHOPPING INTELLIGENCE", heroEyebrow: "PURCHASE INTELLIGENCE", heroTitle: "Check before you buy.",
    heroDescription: "Enter a product name or link. SAVVY checks the match, price, and delivery costs.", sectionEyebrow: "WHAT DO YOU WANT TO CHECK?",
    formTitle: "Add a product or link", productName: "What do you want to find or check?", modeText: "✎ Text", modeLink: "↗ Product link", placeholder: "For example, Nike Air Max T-shirt under $30", linkPlaceholder: "Paste a public link to a product page", paste: "Paste",
    fieldHint: "Enter a product, its key details and budget, or paste a product link.", shipTo: "Deliver to", displayCurrency: "Currency", searchButton: "Check this offer",
    searching: "Finding the best option…", searchingHint: "Comparing matches, prices, and known costs. This may take up to a minute.", conversationHint: "Hi! Tell me which product or gift you are looking for and your budget, and I can compare offers.",
    trustNote: "Some marketplaces can be unreliable. Shipping and duties may be estimates; exchange rates are indicative, so confirm the final price with the seller.",
    privacyNote: "Your query and delivery country are sent to the bot and search providers. The Mini App does not store them in a database.",
    resultsEyebrow: "SEARCH RESULTS", resultsTitle: "Best option", newSearch: "New search", promiseCost: "Total cost",
    promiseSeller: "Seller reliability", promiseMatch: "Product match", footerSlogan: "Shop with confidence.",
    exact: "Exact match", similar: "Similar item", giftIdea: "Gift idea", productPrice: "Item price", totalPrice: "Total with costs", estimatedTotal: "Estimated total*",
    seller: "Seller", shipsFrom: "Ships from", risk: "Risk", dealQuality: "Deal quality score", why: "Why SAVVY picked this option", matched: "Matched details: ",
    matchExactReason: "The available product details match the requested item.", matchSimilarReason: "This is a similar option; an exact match could not be confirmed.",
    lowestTotal: "Lowest confirmed total cost among the matching offers found.", lowestPrice: "Lowest item price among matching offers found; shipping may not be included.",
    qualityTie: "At the same price, this offer has a better quality score based on available data.", riskTie: "At the same cost, this offer has a lower estimated risk.", onlyComparable: "No other price-comparable matching offer was found.",
    details: "Costs and terms", hideDetails: "Hide details", delivery: "Shipping", taxes: "Taxes", duties: "Import duty", unconfirmed: "not confirmed", estimated: " · estimated",
    knownTotalNote: "Calculated from known cost components.", unknownTotalNote: "The full cost is not confirmed. Check the seller's checkout page.",
    openProduct: "Open product", compare: "Compare other options", hideCompare: "Hide comparison", found: "Options found", noOffers: "No reliable priced offers were found yet.",
    refineSearch: "Try adding a brand, model, size, or another key detail.", noPrice: "Price unavailable", pasteUnavailable: "Clipboard is unavailable. Paste the text manually.",
    pasteFailed: "Could not read the clipboard. Paste the text manually.", clipboardEmpty: "The clipboard is empty.", tooShort: "Enter a product name with at least two characters.",
    linksUnsupported: "Paste a public product page link starting with http:// or https://.", openTelegram: "Open the app using ✨ SavvyApp in the bot message or chat menu.",
    helpTitle: "App help", helpBody: "Enter a product name or switch to link mode. Choose a delivery country and currency. SAVVY shows exact matches and known costs; shipping or duties not confirmed by the seller are marked separately.", helpLimits: "Photo search, price history, and automatic alerts are not connected yet.",
    noAlternatives: "No other options yet", searchError: "Search failed. Please try again.", rateLimited: "Too many searches. Please try again in a minute.", invalidSearch: "Check the product name and delivery country.",
    regionNames: { BY: "Belarus", RU: "Russia", KZ: "Kazakhstan", UZ: "Uzbekistan", KG: "Kyrgyzstan", AM: "Armenia", AZ: "Azerbaijan", MD: "Moldova", TJ: "Tajikistan", TM: "Turkmenistan", GE: "Georgia", UA: "Ukraine" },
    attributes: { brand: "brand", model: "model", color: "color", size: "size", storage: "storage", material: "material", category: "category", condition: "condition" },
  },
  be: {
    locale: "be-BY", pageTitle: "SavvyApp — знайдзі найлепшы варыянт", homeAria: "SAVVY — галоўная", promisesAria: "Што правярае SAVVY", beta: "ранні доступ", heroEyebrow: "PURCHASE INTELLIGENCE", heroTitle: "Правер перад пакупкай.",
    heroDescription: "Абяры тавар і краіну дастаўкі. SAVVY шукае прапановы ў даступных рэгіёнах.", sectionEyebrow: "ВАША НАСТУПНАЯ ПАКУПКА",
    formTitle: "Дадайце тавар або спасылку", productName: "Што хочаце знайсці або праверыць?", modeText: "✎ Тэкст", modeLink: "↗ Спасылка на тавар", placeholder: "Напрыклад, футболка Nike да 100 BYN", linkPlaceholder: "Устаўце публічную спасылку на старонку тавару", paste: "Уставіць",
    fieldHint: "Напішы назву, характарыстыкі і бюджэт або ўстаў спасылку на тавар.", shipTo: "Дастаўка", displayCurrency: "Валюта", searchButton: "Праверыць прапанову",
    searching: "Шукаем найлепшы варыянт…", searchingHint: "Параўноўваем супадзенні, цэны і вядомыя выдаткі. Гэта можа заняць да хвіліны.",
    trustNote: "Некаторыя пляцоўкі працуюць нестабільна. Дастаўка і пошліны могуць быць ацэначнымі; курсы валют пакуль арыенціровачныя — правер выніковую цану ў прадаўца.",
    privacyNote: "Запыт і краіна дастаўкі перадаюцца боту і пошукавым пляцоўкам. Mini App не захоўвае іх у базе.",
    resultsEyebrow: "ВЫНІКІ ПОШУКУ", resultsTitle: "Найлепшы варыянт", newSearch: "Новы пошук", promiseCost: "Поўны кошт",
    promiseSeller: "Надзейнасць прадаўца", promiseMatch: "Супадзенне тавару", footerSlogan: "Купляй свядома.",
    exact: "Дакладнае супадзенне", similar: "Падобны тавар", giftIdea: "Ідэя падарунка", productPrice: "Кошт тавару", totalPrice: "Разам з выдаткамі", estimatedTotal: "Ацэнка разам*",
    seller: "Прадавец", shipsFrom: "Адпраўка", risk: "Рызыка", dealQuality: "Ацэнка якасці здзелкі", why: "Чаму SAVVY выбраў гэты варыянт", matched: "Супалі характарыстыкі: ",
    matchExactReason: "Даступныя характарыстыкі супадаюць з патрэбным таварам.", matchSimilarReason: "Гэта падобны варыянт; дакладнае супадзенне не пацверджана.",
    lowestTotal: "Найменшы пацверджаны поўны кошт сярод знойдзеных супадзенняў.", lowestPrice: "Найменшы кошт тавару сярод знойдзеных супадзенняў; дастаўка можа быць не ўлічана.",
    qualityTie: "Пры аднолькавым кошце гэтая прапанова мае лепшую ацэнку якасці паводле наяўных звестак.", riskTie: "Пры аднолькавым кошце ў гэтай прапановы ніжэйшая разліковая рызыка.", onlyComparable: "Іншых супастаўных прапаноў з цаной не знойдзена.",
    details: "Выдаткі і ўмовы", hideDetails: "Схаваць падрабязнасці", delivery: "Дастаўка", taxes: "Падаткі", duties: "Пошліна", unconfirmed: "не пацверджана", estimated: " · ацэнка",
    knownTotalNote: "Разлічана паводле вядомых складнікаў.", unknownTotalNote: "Поўны кошт не пацверджаны. Правер яго на старонцы прадаўца.",
    openProduct: "Адкрыць тавар", compare: "Параўнаць іншыя варыянты", hideCompare: "Схаваць параўнанне", found: "Знойдзена варыянтаў", noOffers: "Пакуль няма надзейных прапаноў з цаной.",
    refineSearch: "Дадай брэнд, мадэль, памер або іншую важную дэталь.", noPrice: "Кошт не пазначаны", pasteUnavailable: "Буфер абмену недаступны. Устаў тэкст уручную.",
    pasteFailed: "Не ўдалося прачытаць буфер абмену. Устаў тэкст уручную.", clipboardEmpty: "Буфер абмену пусты.", tooShort: "Увядзі назву тавару — не менш за два сімвалы.",
    linksUnsupported: "Устаў публічную спасылку на старонку тавару з http:// або https://.", openTelegram: "Адкрый праграму кнопкай ✨ SavvyApp у паведамленні бота або ў меню чата.",
    helpTitle: "Даведка па праграме", helpBody: "Увядзі назву тавару або пераключыся на спасылку. Выберы краіну дастаўкі і валюту. SAVVY пакажа дакладныя супадзенні і вядомыя выдаткі; непацверджаную дастаўку або пошліну пазначыць асобна.", helpLimits: "Пошук па фота, гісторыя цэн і аўтаматычныя апавяшчэнні пакуль не падключаныя.",
    noAlternatives: "Іншых варыянтаў пакуль няма", searchError: "Не ўдалося выканаць пошук. Паспрабуй яшчэ раз.", rateLimited: "Занадта шмат запытаў. Паспрабуй праз хвіліну.", invalidSearch: "Правер назву тавару і краіну дастаўкі.",
    regionNames: { BY: "Беларусь", RU: "Расія", KZ: "Казахстан", UZ: "Узбекістан", KG: "Кыргызстан", AM: "Арменія", AZ: "Азербайджан", MD: "Малдова", TJ: "Таджыкістан" },
    attributes: { brand: "брэнд", model: "мадэль", color: "колер", size: "памер", storage: "памяць", material: "матэрыял", category: "катэгорыя", condition: "стан" },
  },
};

translations.kk = Object.assign({}, translations.en, {
  locale: "kk-KZ", pageTitle: "SavvyApp — тиімді тауарды табыңыз", homeAria: "SAVVY — басты бет", promisesAria: "SAVVY нені тексереді", beta: "AI SHOPPING INTELLIGENCE",
  heroEyebrow: "PURCHASE INTELLIGENCE", heroTitle: "Сатып алмас бұрын тексеріңіз.", heroDescription: "Тауар атауын немесе сілтемесін жіберіңіз. SAVVY сәйкестігін, бағасын және жеткізуін тексереді.",
  sectionEyebrow: "НЕНІ ТЕКСЕРГІҢІЗ КЕЛЕДІ?", formTitle: "Тауарды немесе сілтемені қосыңыз", productName: "Нені іздеп немесе тексергіңіз келеді?", modeText: "✎ Мәтін", modeLink: "↗ Тауар сілтемесі", placeholder: "Мысалы, Nike Air Max жейдесі 15 000 KZT дейін", linkPlaceholder: "Тауар бетінің ашық сілтемесін қойыңыз", paste: "Қою",
  fieldHint: "Тауар атауын, сипаттарын және бюджетін жазыңыз немесе сілтемесін қойыңыз.", shipTo: "Жеткізу елі", displayCurrency: "Валюта", searchButton: "Ұсынысты тексеру",
  searching: "Ең тиімді нұсқа ізделуде…", searchingHint: "Сәйкестіктерді, бағаларды және белгілі шығындарды салыстырамыз. Бір минутқа дейін уақыт алуы мүмкін.", conversationHint: "Сәлем! Қандай тауар не сыйлық іздейтініңізді және бюджетіңізді жазыңыз — ұсыныстарды салыстырамын.",
  trustNote: "Кейбір сауда алаңдары тұрақсыз жұмыс істейді. Жеткізу мен баж салығы шамамен есептелуі мүмкін; соңғы соманы сатушыдан тексеріңіз.",
  privacyNote: "Сұрау мен жеткізу елі Telegram ботына және іздеу сервистеріне жіберіледі. Mini App оларды дерекқорда сақтамайды.",
  resultsEyebrow: "ІЗДЕУ НӘТИЖЕЛЕРІ", resultsTitle: "Ең тиімді нұсқа", newSearch: "Жаңа іздеу", promiseCost: "Толық құны", promiseSeller: "Сатушы сенімділігі", promiseMatch: "Тауар сәйкестігі", footerSlogan: "Сенімді сатып алыңыз.",
  exact: "Дәл сәйкестік", similar: "Ұқсас тауар", giftIdea: "Сыйлық идеясы", productPrice: "Тауар бағасы", totalPrice: "Шығындармен бірге", estimatedTotal: "Шамамен жалпы баға*", seller: "Сатушы", shipsFrom: "Жөнелту орны", risk: "Тәуекел", dealQuality: "Мәміле сапасының бағасы", why: "SAVVY бұл нұсқаны неге таңдады", matched: "Сәйкес сипаттар: ",
  matchExactReason: "Қолжетімді сипаттар сұралған тауарға сәйкес келеді.", matchSimilarReason: "Бұл ұқсас нұсқа; дәл сәйкестік расталмады.", lowestTotal: "Табылған дәл сәйкестіктер арасындағы ең төмен расталған толық баға.", lowestPrice: "Тауардың ең төмен бағасы; жеткізу есепке алынбауы мүмкін.",
  qualityTie: "Бағасы бірдей ұсыныстардың ішінде қолжетімді сапа деректері бойынша бұл нұсқа жоғары.", riskTie: "Бағасы бірдей ұсыныстардың ішінде бұл нұсқаның есептік тәуекелі төмен.", onlyComparable: "Бағасы көрсетілген басқа салыстырмалы ұсыныс табылмады.",
  details: "Шығындар мен шарттар", hideDetails: "Мәліметтерді жасыру", delivery: "Жеткізу", taxes: "Салықтар", duties: "Баж салығы", unconfirmed: "расталмаған", estimated: " · бағалау",
  knownTotalNote: "Сома белгілі шығындар негізінде есептелді.", unknownTotalNote: "Толық құн расталмады. Сатушы бетінен тексеріңіз.", openProduct: "Тауарды ашу", compare: "Басқа нұсқаларды салыстыру", hideCompare: "Салыстыруды жасыру", found: "Табылған нұсқалар", noOffers: "Әзірге бағасы бар сенімді ұсыныс табылмады.",
  refineSearch: "Бренд, модель, өлшем немесе маңызды сипат қосып көріңіз.", noPrice: "Бағасы көрсетілмеген", pasteUnavailable: "Алмасу буфері қолжетімсіз. Мәтінді қолмен қойыңыз.", pasteFailed: "Алмасу буферін оқу мүмкін болмады. Мәтінді қолмен қойыңыз.", clipboardEmpty: "Алмасу буфері бос.", tooShort: "Кемінде екі таңбадан тұратын тауар атауын енгізіңіз.",
  linksUnsupported: "http:// немесе https:// мекенжайынан басталатын тауар бетінің ашық сілтемесін қойыңыз.", openTelegram: "Бот хабарламасындағы немесе чат мәзіріндегі ✨ SavvyApp батырмасымен ашыңыз.", noAlternatives: "Басқа нұсқа әзірше жоқ", searchError: "Іздеу орындалмады. Қайталап көріңіз.", rateLimited: "Сұраулар тым жиі. Бір минуттан кейін қайталап көріңіз.", invalidSearch: "Тауар атауы мен жеткізу елін тексеріңіз.",
  helpTitle: "Қолданба бойынша көмек", helpBody: "Тауар атауын енгізіңіз немесе сілтеме режиміне ауысыңыз. Жеткізу елі мен валютаны таңдаңыз. SAVVY дәл сәйкестіктер мен белгілі шығындарды көрсетеді; расталмаған жеткізу не баж салығын бөлек белгілейді.", helpLimits: "Фото іздеу, баға тарихы және автоматты хабарландырулар әлі қосылмаған.",
  regionNames: { BY: "Беларусь", RU: "Ресей", KZ: "Қазақстан", UZ: "Өзбекстан", KG: "Қырғызстан", AM: "Армения", AZ: "Әзербайжан", MD: "Молдова", TJ: "Тәжікстан", TM: "Түрікменстан", GE: "Грузия", UA: "Украина" },
  attributes: { brand: "бренд", model: "модель", color: "түс", size: "өлшем", storage: "жады", material: "материал", category: "санат", condition: "күйі" },
});

const form = document.querySelector("#offer-form");
const queryInput = document.querySelector("#offer-url");
const message = document.querySelector("#form-message");
const submitButton = form.querySelector("[type='submit']");
const results = document.querySelector("#results");
const bestCard = document.querySelector("#best-card");
const alternatives = document.querySelector("#alternatives");
const compareToggle = document.querySelector("#compare-toggle");
const resultStatus = document.querySelector("#result-status");
const riskNames = {
  ru: { low: "низкий", medium: "средний", high: "высокий", critical: "критический" },
  en: { low: "low", medium: "medium", high: "high", critical: "critical" },
  be: { low: "нізкі", medium: "сярэдні", high: "высокі", critical: "крытычны" },
  kk: { low: "төмен", medium: "орташа", high: "жоғары", critical: "аса жоғары" },
};
let language = "ru";
try {
  const savedLanguage = localStorage.getItem("savvy.language");
  if (["ru", "en", "kk"].includes(savedLanguage)) language = savedLanguage;
} catch {
  // The app still works when browser storage is disabled.
}
const languageSelect = document.querySelector("#language");
const currencySelect = document.querySelector("#currency");
const regionSelect = document.querySelector("#region");
let currentResult = null;
let queryMode = "text";
const regionCurrencies = { BY: "BYN", RU: "RUB", KZ: "KZT", UZ: "UZS", KG: "KGS", AM: "AMD", AZ: "AZN", MD: "MDL", TJ: "TJS", TM: "TMT", GE: "GEL", UA: "UAH" };
try {
  const savedCurrency = localStorage.getItem("savvy.currency");
  const savedRegion = localStorage.getItem("savvy.region");
  if (savedRegion && regionCurrencies[savedRegion]) regionSelect.value = savedRegion;
  if (savedCurrency && [...currencySelect.options].some((option) => option.value === savedCurrency)) currencySelect.value = savedCurrency;
  else currencySelect.value = regionCurrencies[regionSelect.value] || "USD";
} catch {
  currencySelect.value = regionCurrencies[regionSelect.value] || "USD";
}
regionSelect.addEventListener("change", () => {
  currencySelect.value = regionCurrencies[regionSelect.value] || "USD";
  syncLanguageOptions();
  try {
    localStorage.setItem("savvy.region", regionSelect.value);
    localStorage.setItem("savvy.currency", currencySelect.value);
  } catch { /* Preferences stay available for this session. */ }
});
currencySelect.addEventListener("change", () => {
  try { localStorage.setItem("savvy.currency", currencySelect.value); } catch { /* Current selection still works. */ }
});

function t(key) {
  return translations[language][key] || translations.ru[key] || key;
}

function setLanguage(nextLanguage) {
  language = translations[nextLanguage] ? nextLanguage : "ru";
  try {
    localStorage.setItem("savvy.language", language);
  } catch {
    // Language selection remains active for the current session.
  }
  document.documentElement.lang = language;
  document.title = t("pageTitle");
  document.querySelector("#brand-home").setAttribute("aria-label", t("homeAria"));
  document.querySelector("#promises").setAttribute("aria-label", t("promisesAria"));
  languageSelect.value = language;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  queryInput.placeholder = t(queryMode === "url" ? "linkPlaceholder" : "placeholder");
  document.querySelector("#paste-button").setAttribute("aria-label", t("paste"));
  languageSelect.setAttribute("aria-label", language === "ru" ? "Выбрать язык" : language === "kk" ? "Тілді таңдау" : "Choose language");
  document.querySelectorAll("#region option").forEach((option) => {
    option.textContent = translations[language].regionNames[option.value] || option.value;
  });
  document.querySelectorAll("#currency option").forEach((option) => {
    try {
      const displayName = new Intl.DisplayNames([language], { type: "currency" }).of(option.value);
      if (displayName) option.textContent = `${option.value} — ${displayName}`;
    } catch { /* Keep the authored currency label on older browsers. */ }
  });
  submitButton.querySelector("span:first-child").textContent = submitButton.disabled ? t("searching") : t("searchButton");
  if (message.classList.contains("visible")) {
    if (submitButton.disabled) message.textContent = t("searchingHint");
    else message.classList.remove("visible");
  }
  if (!results.hidden && currentResult) renderResult(currentResult);
}

function syncLanguageOptions() {
  [...languageSelect.options].forEach((option) => { option.hidden = false; });
}

languageSelect.addEventListener("change", () => setLanguage(languageSelect.value));
syncLanguageOptions();
setLanguage(language);

document.querySelectorAll(".search-mode").forEach((button) => {
  button.addEventListener("click", () => {
    queryMode = button.dataset.mode === "url" ? "url" : "text";
    document.querySelectorAll(".search-mode").forEach((mode) => {
      const active = mode === button;
      mode.classList.toggle("active", active);
      mode.setAttribute("aria-selected", String(active));
    });
    queryInput.placeholder = t(queryMode === "url" ? "linkPlaceholder" : "placeholder");
    queryInput.focus();
  });
});

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
  message.classList.add("visible");
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function money(value, currency) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return t("noPrice");
  try {
    return new Intl.NumberFormat(translations[language].locale, { style: "currency", currency, maximumFractionDigits: 2 }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency || ""}`.trim();
  }
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function offerCard(offer, isBest = false) {
  const card = element("article", isBest ? "offer-card featured-offer" : "offer-card alternative-card");
  const header = element("div", "offer-card-header");
  const badgeText = offer.match_type === "gift" ? t("giftIdea") : offer.match_type === "exact" || offer.status === "exact" ? t("exact") : t("similar");
  const badge = element("span", "match-badge", badgeText);
  header.append(badge);
  if (offer.gift_category) header.append(element("span", "source-label", offer.gift_category));
  header.append(element("span", "source-label", offer.source));
  card.append(header);
  card.append(element("h3", "offer-title", offer.title));

  const priceGrid = element("div", "offer-prices");
  const itemPrice = element("div", "price-box");
  itemPrice.append(element("span", "price-caption", t("productPrice")));
  itemPrice.append(element("strong", "item-price", money(offer.price, offer.currency)));
  const totalPrice = element("div", "price-box total-box");
  totalPrice.append(element("span", "price-caption", offer.total_known ? t("totalPrice") : t("estimatedTotal")));
  totalPrice.append(element("strong", "total-price", money(offer.total, offer.currency)));
  priceGrid.append(itemPrice, totalPrice);
  card.append(priceGrid);

  const meta = element("div", "offer-meta");
  if (offer.seller) meta.append(element("span", "meta-chip", `${t("seller")}: ${offer.seller}`));
  if (offer.region) meta.append(element("span", "meta-chip", `${t("shipsFrom")}: ${translations[language].regionNames[offer.region] || offer.region}`));
  if (offer.risk && offer.risk !== "unknown") meta.append(element("span", `meta-chip risk-${offer.risk}`, `${t("risk")}: ${riskNames[language][offer.risk] || offer.risk}`));
  if (offer.quality_known && Number.isFinite(Number(offer.quality))) {
    meta.append(element("span", "meta-chip quality-chip", `${t("dealQuality")}: ${Math.round(Number(offer.quality) * 100)}/100`));
  }
  if (meta.childElementCount) card.append(meta);

  if (isBest && Array.isArray(offer.reason_codes) && offer.reason_codes.length) {
    const why = element("div", "why-box");
    why.append(element("h4", "why-title", t("why")));
    const list = element("ul", "why-list");
    const codes = offer.reason_codes || [];
    codes.forEach((code) => {
      const key = { exact_match: "matchExactReason", similar_match: "matchSimilarReason", lowest_total: "lowestTotal", lowest_price: "lowestPrice", quality_tiebreak: "qualityTie", risk_tiebreak: "riskTie", only_comparable: "onlyComparable" }[code];
      if (key) list.append(element("li", "", t(key)));
    });
    const matched = (offer.matched_attributes || []).map((name) => translations[language].attributes[name] || name);
    if (matched.length) list.append(element("li", "", t("matched") + matched.join(", ") + "."));
    why.append(list);
    card.append(why);
  }

  const actions = element("div", "offer-actions");
  const detailsButton = element("button", "detail-button", t("details"));
  detailsButton.type = "button";
  detailsButton.setAttribute("aria-expanded", "false");
  const details = element("div", "cost-details");
  details.hidden = true;
  [[t("delivery"), offer.delivery, offer.delivery_estimated], [t("taxes"), offer.taxes, offer.taxes_estimated], [t("duties"), offer.duties, offer.duties_estimated]].forEach(([label, value, estimated]) => {
    const amount = value === null || value === undefined ? t("unconfirmed") : money(value, offer.currency) + (estimated ? t("estimated") : "");
    details.append(element("span", "cost-line", `${label}: ${amount}`));
  });
  details.append(element("span", "cost-note", offer.total_known ? t("knownTotalNote") : t("unknownTotalNote")));
  detailsButton.addEventListener("click", () => {
    details.hidden = !details.hidden;
    detailsButton.setAttribute("aria-expanded", String(!details.hidden));
    detailsButton.textContent = details.hidden ? t("details") : t("hideDetails");
  });
  actions.append(detailsButton);
  const href = safeUrl(offer.url);
  if (href) {
    const buyButton = element("a", "buy-button", t("openProduct"));
    buyButton.href = href;
    buyButton.target = "_blank";
    buyButton.rel = "noopener noreferrer";
    buyButton.addEventListener("click", (event) => {
      if (telegram && typeof telegram.openLink === "function") {
        event.preventDefault();
        telegram.openLink(href);
      }
    });
    actions.append(buyButton);
  }
  card.append(actions, details);
  return card;
}

function renderResult(data) {
  currentResult = data;
  results.hidden = false;
  resultStatus.textContent = data.best
    ? `${t("found")}: ${data.found_count} · ${data.query}`
    : t("noOffers");
  bestCard.replaceChildren();
  alternatives.replaceChildren();
  if (!data.best) {
    bestCard.append(element("div", "empty-state", t("refineSearch")));
    compareToggle.hidden = true;
  } else {
    bestCard.append(offerCard(data.best, true));
    const choices = data.alternatives || [];
    choices.forEach((offer) => alternatives.append(offerCard(offer)));
    compareToggle.hidden = alternatives.childElementCount === 0;
    alternatives.hidden = true;
    compareToggle.setAttribute("aria-expanded", "false");
    compareToggle.textContent = `${t("compare")} (${choices.length})`;
  }
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#paste-button").addEventListener("click", async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      showMessage(t("pasteUnavailable"));
      return;
    }
    const clipboardText = await navigator.clipboard.readText();
    if (clipboardText) {
      queryInput.value = clipboardText.trim();
      queryInput.focus();
      message.classList.remove("visible");
    } else showMessage(t("clipboardEmpty"));
  } catch {
    showMessage(t("pasteFailed"));
  }
});

queryInput.addEventListener("input", () => message.classList.remove("visible"));
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (query.length < 2) {
    showMessage(t("tooShort"), true);
    queryInput.focus();
    return;
  }
  if (/^(?:привет|здравствуй|здравствуйте|доброе утро|добрый день|добрый вечер|как дела|как ты|что нового|спасибо|пока|hello|hi|hey|how are you|good morning|good afternoon|good evening|thanks|thank you|bye|сәлем|сәлеметсіз бе|қалайсың|қалыңыз қалай|рақмет|сау бол)(?:[!?.,\s]+(?:как дела|как ты|что нового|how are you|қалайсың|қалыңыз қалай))*[!?.,\s]*$/i.test(query)) {
    showMessage(t("conversationHint"));
    return;
  }
  if (queryMode === "url" && !/^https?:\/\//i.test(query)) {
    showMessage(t("linksUnsupported"), true);
    return;
  }
  if (!telegram || !telegram.initData) {
    showMessage(t("openTelegram"), true);
    return;
  }

  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = t("searching");
  showMessage(t("searchingHint"));
  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": telegram.initData,
      },
      body: JSON.stringify({ query, region: regionSelect.value, currency: currencySelect.value }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(
      response.status === 401 ? t("openTelegram") :
        response.status === 429 ? t("rateLimited") :
      response.status === 400 ? payload.error || t("invalidSearch") : t("searchError"),
    );
    message.classList.remove("visible");
    renderResult(payload);
  } catch (error) {
    const errorText = error instanceof Error && error.message !== "Failed to fetch" ? error.message : t("searchError");
    showMessage(errorText, true);
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = t("searchButton");
  }
});

compareToggle.addEventListener("click", () => {
  alternatives.hidden = !alternatives.hidden;
  compareToggle.setAttribute("aria-expanded", String(!alternatives.hidden));
  compareToggle.textContent = alternatives.hidden
    ? `${t("compare")} (${alternatives.childElementCount})`
    : t("hideCompare");
});

document.querySelector("#new-search").addEventListener("click", () => {
  resetSearch();
  queryInput.focus();
  document.querySelector("#check-title").scrollIntoView({ behavior: "smooth", block: "start" });
});

function resetSearch() {
  queryInput.value = "";
  results.hidden = true;
  currentResult = null;
  message.classList.remove("visible");
}

document.querySelector("#brand-home").addEventListener("click", (event) => {
  event.preventDefault();
  resetSearch();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
