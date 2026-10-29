"use strict";

const telegram = window.Telegram && window.Telegram.WebApp;
if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor("#f5f4ef");
  telegram.setBackgroundColor("#f5f4ef");
}

const form = document.querySelector("#offer-form");
const urlInput = document.querySelector("#offer-url");
const message = document.querySelector("#form-message");

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("error", isError);
  message.classList.add("visible");
}

document.querySelector("#paste-button").addEventListener("click", async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      showMessage("Буфер обмена недоступен. Вставьте ссылку в поле вручную.");
      return;
    }
    const clipboardText = await navigator.clipboard.readText();
    if (clipboardText) {
      urlInput.value = clipboardText.trim();
      urlInput.focus();
      message.classList.remove("visible");
    } else {
      showMessage("Буфер обмена пуст. Скопируйте ссылку и попробуйте ещё раз.");
    }
  } catch {
    showMessage("Telegram или браузер не разрешил доступ к буферу. Вставьте ссылку вручную.");
  }
});

urlInput.addEventListener("input", () => message.classList.remove("visible"));
form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = urlInput.value.trim();
  if (query.length < 2) {
    showMessage("Напишите название товара — хотя бы два символа.", true);
    urlInput.focus();
    return;
  }

  if (/^(https?:\/\/|www\.)/i.test(query)) {
    showMessage("Пока SAVVY ищет по названию товара. Проверку конкретных ссылок подключим отдельно.", true);
    return;
  }

  if (!telegram || typeof telegram.sendData !== "function") {
    showMessage("Открой SAVVY через Telegram, чтобы отправить запрос боту.", true);
    return;
  }

  const region = document.querySelector("#region").value;
  telegram.sendData(JSON.stringify({ query, region }));
});
