# Telegram Bot Shop 🛒

An asynchronous Telegram e-commerce bot built with **Python 3** and the **Aiogram 3** framework, designed to automate online sales directly within the messenger.

The project is fully optimized for production deployment on a Linux server, running as a highly reliable, self-healing background service managed by **systemd**.

---

## 🚀 Features

* **Interactive Catalog:** Clean navigation through product categories with image support and detailed descriptions.
* **Shopping Cart:** Flexible cart management (add, update quantities, remove items) before checkout.
* **Automated Checkout:** Seamless order processing with instant notifications sent directly to the administrator.
* **Production Ready:** Run-configured with Python virtual environments (`venv`) and automated crash recovery via systemd.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Framework:** Aiogram 3.x (Asynchronous Telegram Bot API)
* **OS Target:** Linux (Ubuntu/Debian)
* **Process Manager:** Systemd
* **Environment:** Virtualenv (venv)

---

## 📁 Project Structure

```text
03_bot_shop/
├── handlers/             # Bot message handlers & routers
├── pictures/             # Media assets and product images
├── venv/                 # Local Python virtual environment
├── main.py               # Main entry point of the bot
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

1.  Clone the repository

```bash
git clone [https://github.com/yourusername/03_bot_shop.git](https://github.com/yourusername/03_bot_shop.git)
cd 03_bot_shop
```

2. Set up the virtual environment

To keep dependencies isolated, create and activate a local virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```
