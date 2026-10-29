"use strict";

const telegram = window.Telegram && window.Telegram.WebApp;
if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor("#f5f4ef");
  telegram.setBackgroundColor("#f5f4ef");
}

const translations = {
  ru: {
    locale: "ru-RU", pageTitle: "SavvyApp — найди лучший вариант", homeAria: "SAVVY — главная", promisesAria: "Что SAVVY проверяет", beta: "ранний доступ", heroEyebrow: "ПОИСК ПЕРЕД ПОКУПКОЙ", heroTitle: "Сравни, прежде чем купить.",
    heroDescription: "Укажи товар и страну доставки. SAVVY поищет предложения в нескольких регионах.", sectionEyebrow: "ВАША СЛЕДУЮЩАЯ ПОКУПКА",
    formTitle: "Что хотите найти?", productName: "Название товара", placeholder: "Например, футболка Nike Air Max", paste: "Вставить",
    fieldHint: "Напиши модель и важные детали — покажем лучший найденный вариант.", shipTo: "Куда доставлять?", searchButton: "Найти лучший вариант",
    searching: "Ищем лучший вариант…", searchingHint: "Сравниваем совпадения, цены и известные расходы. Это может занять до минуты.",
    trustNote: "Часть площадок работает нестабильно. Стоимость доставки и пошлин иногда оценивается, а не подтверждается продавцом.",
    privacyNote: "Название и выбранная страна отправляются Telegram-боту и поисковым площадкам. Mini App не сохраняет их в базе.",
    resultsEyebrow: "РЕЗУЛЬТАТ ПОИСКА", resultsTitle: "Лучший вариант", newSearch: "Новый поиск", promiseCost: "Итоговая стоимость",
    promiseSeller: "Надёжность продавца", promiseMatch: "Совпадение товара", footerSlogan: "Покупай осознанно.",
    exact: "Точное совпадение", similar: "Похожий товар", productPrice: "Цена товара", totalPrice: "Итого с расходами", estimatedTotal: "Оценка итого*",
    seller: "Продавец", shipsFrom: "Отправка", risk: "Риск", why: "Почему SAVVY выбрал этот вариант", matched: "Совпали характеристики: ",
    matchExactReason: "Совпадение товара подтверждено по найденным характеристикам.", matchSimilarReason: "Это близкий вариант: полное совпадение подтвердить не удалось.",
    lowestTotal: "Минимальная подтверждённая полная стоимость среди найденных совпадений.", lowestPrice: "Минимальная цена товара среди найденных совпадений; доставка могла быть не учтена.",
    qualityTie: "При одинаковой цене у предложения лучше оценка качества по доступным данным.", riskTie: "При одинаковой стоимости у предложения ниже расчётный риск.", onlyComparable: "Других сравнимых предложений с ценой не найдено.",
    details: "Расходы и условия", hideDetails: "Скрыть подробности", delivery: "Доставка", taxes: "Налоги", duties: "Пошлина", unconfirmed: "не подтверждена", estimated: " · оценка",
    knownTotalNote: "Сумма рассчитана по известным компонентам.", unknownTotalNote: "Полная стоимость не подтверждена. Проверь сумму на странице продавца.",
    openProduct: "Открыть товар", compare: "Сравнить другие варианты", hideCompare: "Скрыть сравнение", found: "Найдено вариантов", noOffers: "Надёжных предложений с ценой пока нет.",
    refineSearch: "Попробуй добавить бренд, модель, размер или другую важную деталь.", noPrice: "Цена не указана", pasteUnavailable: "Буфер обмена недоступен. Вставь текст в поле вручную.",
    pasteFailed: "Не удалось прочитать буфер обмена. Вставь текст вручную.", clipboardEmpty: "Буфер обмена пуст.", tooShort: "Напиши название товара — хотя бы два символа.",
    linksUnsupported: "Пока поиск работает по названию, а не по ссылке.", openTelegram: "Открой приложение кнопкой ✨ SavvyApp в сообщении бота или в меню чата.",
    noAlternatives: "Других вариантов пока нет", searchError: "Не удалось выполнить поиск. Попробуй ещё раз.", rateLimited: "Слишком много запросов. Попробуй через минуту.", invalidSearch: "Проверь название товара и страну доставки.",
    regionNames: { BY: "Беларусь", RU: "Россия", KZ: "Казахстан", UZ: "Узбекистан", KG: "Кыргызстан", AM: "Армения", AZ: "Азербайджан", MD: "Молдова" },
    attributes: { brand: "бренд", model: "модель", color: "цвет", size: "размер", storage: "память", material: "материал", category: "категория", condition: "состояние" },
  },
  en: {
    locale: "en-US", pageTitle: "SavvyApp — find the best option", homeAria: "SAVVY — home", promisesAria: "What SAVVY checks", beta: "early access", heroEyebrow: "SEARCH BEFORE YOU BUY", heroTitle: "Compare before you buy.",
    heroDescription: "Choose an item and delivery country. SAVVY searches offers across supported regions.", sectionEyebrow: "YOUR NEXT PURCHASE",
    formTitle: "What are you looking for?", productName: "Product name", placeholder: "For example, Nike Air Max T-shirt", paste: "Paste",
    fieldHint: "Add the model and key details to find the best available match.", shipTo: "Deliver to", searchButton: "Find the best option",
    searching: "Finding the best option…", searchingHint: "Comparing matches, prices, and known costs. This may take up to a minute.",
    trustNote: "Some marketplaces can be unreliable. Shipping and duties may be estimates rather than seller-confirmed amounts.",
    privacyNote: "Your query and delivery country are sent to the bot and search providers. The Mini App does not store them in a database.",
    resultsEyebrow: "SEARCH RESULTS", resultsTitle: "Best option", newSearch: "New search", promiseCost: "Total cost",
    promiseSeller: "Seller reliability", promiseMatch: "Product match", footerSlogan: "Shop with confidence.",
    exact: "Exact match", similar: "Similar item", productPrice: "Item price", totalPrice: "Total with costs", estimatedTotal: "Estimated total*",
    seller: "Seller", shipsFrom: "Ships from", risk: "Risk", why: "Why SAVVY picked this option", matched: "Matched details: ",
    matchExactReason: "The available product details match the requested item.", matchSimilarReason: "This is a similar option; an exact match could not be confirmed.",
    lowestTotal: "Lowest confirmed total cost among the matching offers found.", lowestPrice: "Lowest item price among matching offers found; shipping may not be included.",
    qualityTie: "At the same price, this offer has a better quality score based on available data.", riskTie: "At the same cost, this offer has a lower estimated risk.", onlyComparable: "No other price-comparable matching offer was found.",
    details: "Costs and terms", hideDetails: "Hide details", delivery: "Shipping", taxes: "Taxes", duties: "Import duty", unconfirmed: "not confirmed", estimated: " · estimated",
    knownTotalNote: "Calculated from known cost components.", unknownTotalNote: "The full cost is not confirmed. Check the seller's checkout page.",
    openProduct: "Open product", compare: "Compare other options", hideCompare: "Hide comparison", found: "Options found", noOffers: "No reliable priced offers were found yet.",
    refineSearch: "Try adding a brand, model, size, or another key detail.", noPrice: "Price unavailable", pasteUnavailable: "Clipboard is unavailable. Paste the text manually.",
    pasteFailed: "Could not read the clipboard. Paste the text manually.", clipboardEmpty: "The clipboard is empty.", tooShort: "Enter a product name with at least two characters.",
    linksUnsupported: "Search by product name is available; link checks are not yet supported.", openTelegram: "Open the app using ✨ SavvyApp in the bot message or chat menu.",
    noAlternatives: "No other options yet", searchError: "Search failed. Please try again.", rateLimited: "Too many searches. Please try again in a minute.", invalidSearch: "Check the product name and delivery country.",
    regionNames: { BY: "Belarus", RU: "Russia", KZ: "Kazakhstan", UZ: "Uzbekistan", KG: "Kyrgyzstan", AM: "Armenia", AZ: "Azerbaijan", MD: "Moldova" },
    attributes: { brand: "brand", model: "model", color: "color", size: "size", storage: "storage", material: "material", category: "category", condition: "condition" },
  },
  be: {
    locale: "be-BY", pageTitle: "SavvyApp — знайдзі найлепшы варыянт", homeAria: "SAVVY — галоўная", promisesAria: "Што правярае SAVVY", beta: "ранні доступ", heroEyebrow: "ПОШУК ПЕРАД ПАКУПКАЙ", heroTitle: "Параўнай, перш чым купіць.",
    heroDescription: "Абяры тавар і краіну дастаўкі. SAVVY шукае прапановы ў даступных рэгіёнах.", sectionEyebrow: "ВАША НАСТУПНАЯ ПАКУПКА",
    formTitle: "Што шукаем?", productName: "Назва тавару", placeholder: "Напрыклад, футболка Nike Air Max", paste: "Уставіць",
    fieldHint: "Дадай мадэль і важныя дэталі, каб знайсці найлепшы варыянт.", shipTo: "Куды даставіць?", searchButton: "Знайсці найлепшы варыянт",
    searching: "Шукаем найлепшы варыянт…", searchingHint: "Параўноўваем супадзенні, цэны і вядомыя выдаткі. Гэта можа заняць да хвіліны.",
    trustNote: "Некаторыя пляцоўкі працуюць нестабільна. Кошт дастаўкі і пошлін можа быць ацэначным, а не пацверджаным прадаўцом.",
    privacyNote: "Запыт і краіна дастаўкі перадаюцца боту і пошукавым пляцоўкам. Mini App не захоўвае іх у базе.",
    resultsEyebrow: "ВЫНІКІ ПОШУКУ", resultsTitle: "Найлепшы варыянт", newSearch: "Новы пошук", promiseCost: "Поўны кошт",
    promiseSeller: "Надзейнасць прадаўца", promiseMatch: "Супадзенне тавару", footerSlogan: "Купляй свядома.",
    exact: "Дакладнае супадзенне", similar: "Падобны тавар", productPrice: "Кошт тавару", totalPrice: "Разам з выдаткамі", estimatedTotal: "Ацэнка разам*",
    seller: "Прадавец", shipsFrom: "Адпраўка", risk: "Рызыка", why: "Чаму SAVVY выбраў гэты варыянт", matched: "Супалі характарыстыкі: ",
    matchExactReason: "Даступныя характарыстыкі супадаюць з патрэбным таварам.", matchSimilarReason: "Гэта падобны варыянт; дакладнае супадзенне не пацверджана.",
    lowestTotal: "Найменшы пацверджаны поўны кошт сярод знойдзеных супадзенняў.", lowestPrice: "Найменшы кошт тавару сярод знойдзеных супадзенняў; дастаўка можа быць не ўлічана.",
    qualityTie: "Пры аднолькавым кошце гэтая прапанова мае лепшую ацэнку якасці паводле наяўных звестак.", riskTie: "Пры аднолькавым кошце ў гэтай прапановы ніжэйшая разліковая рызыка.", onlyComparable: "Іншых супастаўных прапаноў з цаной не знойдзена.",
    details: "Выдаткі і ўмовы", hideDetails: "Схаваць падрабязнасці", delivery: "Дастаўка", taxes: "Падаткі", duties: "Пошліна", unconfirmed: "не пацверджана", estimated: " · ацэнка",
    knownTotalNote: "Разлічана паводле вядомых складнікаў.", unknownTotalNote: "Поўны кошт не пацверджаны. Правер яго на старонцы прадаўца.",
    openProduct: "Адкрыць тавар", compare: "Параўнаць іншыя варыянты", hideCompare: "Схаваць параўнанне", found: "Знойдзена варыянтаў", noOffers: "Пакуль няма надзейных прапаноў з цаной.",
    refineSearch: "Дадай брэнд, мадэль, памер або іншую важную дэталь.", noPrice: "Кошт не пазначаны", pasteUnavailable: "Буфер абмену недаступны. Устаў тэкст уручную.",
    pasteFailed: "Не ўдалося прачытаць буфер абмену. Устаў тэкст уручную.", clipboardEmpty: "Буфер абмену пусты.", tooShort: "Увядзі назву тавару — не менш за два сімвалы.",
    linksUnsupported: "Пакуль пошук працуе па назве тавару, а не па спасылцы.", openTelegram: "Адкрый праграму кнопкай ✨ SavvyApp у паведамленні бота або ў меню чата.",
    noAlternatives: "Іншых варыянтаў пакуль няма", searchError: "Не ўдалося выканаць пошук. Паспрабуй яшчэ раз.", rateLimited: "Занадта шмат запытаў. Паспрабуй праз хвіліну.", invalidSearch: "Правер назву тавару і краіну дастаўкі.",
    regionNames: { BY: "Беларусь", RU: "Расія", KZ: "Казахстан", UZ: "Узбекістан", KG: "Кыргызстан", AM: "Арменія", AZ: "Азербайджан", MD: "Малдова" },
    attributes: { brand: "брэнд", model: "мадэль", color: "колер", size: "памер", storage: "памяць", material: "матэрыял", category: "катэгорыя", condition: "стан" },
  },
};

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
};
let language = "ru";
try {
  const savedLanguage = localStorage.getItem("savvy.language");
  if (translations[savedLanguage]) language = savedLanguage;
} catch {
  // The app still works when browser storage is disabled.
}
const languageSelect = document.querySelector("#language");
let currentResult = null;

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
  document.documentElement.lang = language === "be" ? "be" : language;
  document.title = t("pageTitle");
  document.querySelector("#brand-home").setAttribute("aria-label", t("homeAria"));
  document.querySelector("#promises").setAttribute("aria-label", t("promisesAria"));
  languageSelect.value = language;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  queryInput.placeholder = t("placeholder");
  document.querySelector("#paste-button").setAttribute("aria-label", t("paste"));
  languageSelect.setAttribute("aria-label", language === "ru" ? "Выбрать язык" : language === "be" ? "Выбраць мову" : "Choose language");
  document.querySelectorAll("#region option").forEach((option) => {
    option.textContent = translations[language].regionNames[option.value] || option.value;
  });
  submitButton.querySelector("span:first-child").textContent = submitButton.disabled ? t("searching") : t("searchButton");
  if (message.classList.contains("visible")) {
    if (submitButton.disabled) message.textContent = t("searchingHint");
    else message.classList.remove("visible");
  }
  if (!results.hidden && currentResult) renderResult(currentResult);
}

languageSelect.addEventListener("change", () => setLanguage(languageSelect.value));
setLanguage(language);

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
  const badge = element("span", "match-badge", offer.match_type === "exact" || offer.status === "exact" ? t("exact") : t("similar"));
  header.append(badge);
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
  if (/^(https?:\/\/|www\.)/i.test(query)) {
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
      body: JSON.stringify({ query, region: document.querySelector("#region").value }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(
      response.status === 401 ? t("openTelegram") :
        response.status === 429 ? t("rateLimited") :
          response.status === 400 ? t("invalidSearch") : t("searchError"),
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
