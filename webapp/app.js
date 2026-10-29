"use strict";

const telegram = window.Telegram && window.Telegram.WebApp;
if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor("#f5f4ef");
  telegram.setBackgroundColor("#f5f4ef");
}

const form = document.querySelector("#offer-form");
const queryInput = document.querySelector("#offer-url");
const message = document.querySelector("#form-message");
const submitButton = form.querySelector("[type='submit']");
const results = document.querySelector("#results");
const bestCard = document.querySelector("#best-card");
const alternatives = document.querySelector("#alternatives");
const compareToggle = document.querySelector("#compare-toggle");
const resultStatus = document.querySelector("#result-status");
const regionNames = Object.fromEntries(
  [...document.querySelector("#region").options].map((option) => [option.value, option.textContent]),
);
const riskNames = { low: "низкий", medium: "средний", high: "высокий", critical: "критический", unknown: "неизвестен" };

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
  if (!Number.isFinite(amount)) return "Цена не указана";
  try {
    return new Intl.NumberFormat("ru-RU", { style: "currency", currency, maximumFractionDigits: 2 }).format(amount);
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
  const badge = element("span", "match-badge", offer.match_type || "Вариант");
  header.append(badge);
  header.append(element("span", "source-label", offer.source));
  card.append(header);
  card.append(element("h3", "offer-title", offer.title));

  const priceGrid = element("div", "offer-prices");
  const itemPrice = element("div", "price-box");
  itemPrice.append(element("span", "price-caption", "Цена товара"));
  itemPrice.append(element("strong", "item-price", money(offer.price, offer.currency)));
  const totalPrice = element("div", "price-box total-box");
  totalPrice.append(element("span", "price-caption", offer.total_known ? "Итого с расходами" : "Оценка итого*"));
  totalPrice.append(element("strong", "total-price", money(offer.total, offer.currency)));
  priceGrid.append(itemPrice, totalPrice);
  card.append(priceGrid);

  const meta = element("div", "offer-meta");
  if (offer.seller) meta.append(element("span", "meta-chip", `Продавец: ${offer.seller}`));
  if (offer.region) meta.append(element("span", "meta-chip", `Отправка: ${regionNames[offer.region] || offer.region}`));
  if (offer.risk && offer.risk !== "unknown") meta.append(element("span", `meta-chip risk-${offer.risk}`, `Риск: ${riskNames[offer.risk] || "неизвестен"}`));
  if (meta.childElementCount) card.append(meta);

  if (isBest && Array.isArray(offer.why) && offer.why.length) {
    const why = element("div", "why-box");
    why.append(element("h4", "why-title", "Почему SAVVY выбрал этот вариант"));
    const list = element("ul", "why-list");
    offer.why.forEach((reason) => list.append(element("li", "", reason)));
    why.append(list);
    card.append(why);
  }

  const actions = element("div", "offer-actions");
  const detailsButton = element("button", "detail-button", "Расходы и условия");
  detailsButton.type = "button";
  detailsButton.setAttribute("aria-expanded", "false");
  const details = element("div", "cost-details");
  details.hidden = true;
  [["Доставка", offer.delivery, offer.delivery_estimated], ["Налоги", offer.taxes, offer.taxes_estimated], ["Пошлина", offer.duties, offer.duties_estimated]].forEach(([label, value, estimated]) => {
    const amount = value === null || value === undefined ? "не подтверждена" : money(value, offer.currency) + (estimated ? " · оценка" : "");
    details.append(element("span", "cost-line", `${label}: ${amount}`));
  });
  details.append(element("span", "cost-note", offer.total_known ? "Сумма рассчитана по известным компонентам." : "Полная стоимость пока не подтверждена. Проверь сумму на странице продавца."));
  detailsButton.addEventListener("click", () => {
    details.hidden = !details.hidden;
    detailsButton.setAttribute("aria-expanded", String(!details.hidden));
    detailsButton.textContent = details.hidden ? "Расходы и условия" : "Скрыть подробности";
  });
  actions.append(detailsButton);
  const href = safeUrl(offer.url);
  if (href) {
    const buyButton = element("a", "buy-button", "Открыть товар");
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
  results.hidden = false;
  resultStatus.textContent = data.best
    ? `Нашли ${data.found_count} подходящих вариантов для «${data.query}»`
    : (data.message || "Подходящих предложений пока нет.");
  bestCard.replaceChildren();
  alternatives.replaceChildren();
  if (!data.best) {
    bestCard.append(element("div", "empty-state", "Попробуй добавить бренд, модель, размер или другой важный параметр."));
    compareToggle.hidden = true;
  } else {
    bestCard.append(offerCard(data.best, true));
    (data.alternatives || []).forEach((offer) => alternatives.append(offerCard(offer)));
    compareToggle.hidden = alternatives.childElementCount === 0;
    alternatives.hidden = true;
    compareToggle.setAttribute("aria-expanded", "false");
    compareToggle.textContent = `Сравнить другие варианты${data.alternatives.length ? ` (${data.alternatives.length})` : ""}`;
  }
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.querySelector("#paste-button").addEventListener("click", async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      showMessage("Буфер обмена недоступен. Вставь текст в поле вручную.");
      return;
    }
    const clipboardText = await navigator.clipboard.readText();
    if (clipboardText) {
      queryInput.value = clipboardText.trim();
      queryInput.focus();
      message.classList.remove("visible");
    } else showMessage("Буфер обмена пуст.");
  } catch {
    showMessage("Не удалось прочитать буфер обмена. Вставь текст вручную.");
  }
});

queryInput.addEventListener("input", () => message.classList.remove("visible"));
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = queryInput.value.trim();
  if (query.length < 2) {
    showMessage("Напиши название товара — хотя бы два символа.", true);
    queryInput.focus();
    return;
  }
  if (/^(https?:\/\/|www\.)/i.test(query)) {
    showMessage("Пока поиск работает по названию, а не по ссылке.", true);
    return;
  }
  if (!telegram || !telegram.initData) {
    showMessage("Открой Mini App через кнопку в сообщении /start или кнопку SAVVY в меню.", true);
    return;
  }

  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = "Ищем лучший вариант…";
  showMessage("Сравниваем совпадения, цены и известные расходы. Это может занять до минуты.");
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
    if (!response.ok) throw new Error(payload.error || "Поиск не завершился. Попробуй ещё раз.");
    message.classList.remove("visible");
    renderResult(payload);
  } catch (error) {
    showMessage(error instanceof Error ? error.message : "Не удалось выполнить поиск. Попробуй ещё раз.", true);
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = "Найти лучший вариант";
  }
});

compareToggle.addEventListener("click", () => {
  alternatives.hidden = !alternatives.hidden;
  compareToggle.setAttribute("aria-expanded", String(!alternatives.hidden));
  compareToggle.textContent = alternatives.hidden
    ? `Сравнить другие варианты (${alternatives.childElementCount})`
    : "Скрыть сравнение";
});

document.querySelector("#new-search").addEventListener("click", () => {
  queryInput.focus();
  document.querySelector("#check-title").scrollIntoView({ behavior: "smooth", block: "start" });
});
