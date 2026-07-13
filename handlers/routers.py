import os
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router()

PRODUCTS = {
    "electronics": [
        {
            "id": 101, 
            "name": "Gaming Mouse", 
            "price": 1500, 
            "desc": "RGB lighting, 16000 DPI, perfect for competitive gaming.",
            "photo": "pictures/mouse.jpg"
        },
        {
            "id": 102, 
            "name": "Mechanical Keyboard", 
            "price": 3500, 
            "desc": "Red switches, custom keycaps, satisfying typing experience.",
            "photo": "pictures/keyboard.jpg"
        }
    ],
    "clothes": [
        {
            "id": 201, 
            "name": "Hoodie 'Senior Python'", 
            "price": 2200, 
            "desc": "Oversized, 100% cotton, keeps you warm during late-night debugging.",
            "photo": "pictures/hoodie.jpg"
        },
        {
            "id": 202, 
            "name": "T-Shirt 'Bug Feature'", 
            "price": 1000, 
            "desc": "Stylish black t-shirt for true coders.",
            "photo": "pictures/tshirt.jpg"
        }
    ]
}

user_carts = {}
users_base = set()    
total_orders_count = 0  

class OrderProcess(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()

class AdminProcess(StatesGroup):
    waiting_for_broadcast = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    users_base.add(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Catalog", callback_data="open_catalog")],
        [InlineKeyboardButton(text="🛒 My Cart", callback_data="open_cart")]
    ])
    await message.answer(
        f"👋 Hello, {message.from_user.first_name}!\nWelcome to our Telegram Shop.",
        reply_markup=keyboard
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    try:
        admin_id = int(os.getenv("ADMIN_ID", 0))
    except ValueError:
        admin_id = 0

    logging.info(f"Admin command triggered. User ID: {message.from_user.id} | Allowed Admin ID: {admin_id}")

    if message.from_user.id != admin_id:
        await message.answer("❌ Access denied! You are not an admin.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Bot Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Create Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="❌ Close Panel", callback_data="admin_close")]
    ])
    await message.answer("🛠️ *Welcome to the Admin Panel!*", reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if callback.from_user.id != admin_id:
        return

    text = (
        "📊 *Shop Statistics:*\n\n"
        f"👥 Total unique users: {len(users_base)}\n"
        f"📦 Successfully placed orders: {total_orders_count}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if callback.from_user.id != admin_id:
        return

    await state.set_state(AdminProcess.waiting_for_broadcast)
    await callback.message.edit_text("📢 Enter the text for the broadcast to all users:")
    await callback.answer()


@router.message(AdminProcess.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    broadcast_text = message.text
    await state.clear()
    
    success_count = 0
    logging.info(f"Starting mass broadcast to {len(users_base)} users...")
    
    for u_id in users_base:
        try:
            await message.bot.send_message(
                chat_id=u_id, 
                text=f"📢 *Announcement from the shop!*\n\n{broadcast_text}", 
                parse_mode="Markdown"
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.debug(f"Failed to send broadcast message to {u_id}: {e}")
            
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ To Admin Panel", callback_data="back_to_admin")]
    ])
    await message.answer(
        f"✅ Broadcast completed!\nSuccessfully sent: {success_count}/{len(users_base)} messages.", 
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Bot Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Create Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="❌ Close Panel", callback_data="admin_close")]
    ])
    await callback.message.edit_text("🛠️ *Welcome to the Admin Panel!*", reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Admin Panel closed.")


@router.callback_query(F.data == "open_catalog")
async def open_catalog(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Electronics", callback_data="cat_electronics")],
        [InlineKeyboardButton(text="👕 Clothes", callback_data="cat_clothes")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("Select a product category:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    products_list = PRODUCTS.get(category, [])
    
    buttons = []
    for p in products_list:
        buttons.append([InlineKeyboardButton(text=f"{p['name']} — {p['price']} UAH", callback_data=f"prod_{category}_{p['id']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back to Catalog", callback_data="open_catalog")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer("Select a product to view:", reply_markup=keyboard)
    else:
        await callback.message.edit_text("Select a product to view:", reply_markup=keyboard)
        
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def view_product(callback: CallbackQuery):
    data = callback.data.split("_")
    category = data[1]
    prod_id = int(data[2])
    
    product = next((p for p in PRODUCTS[category] if p["id"] == prod_id), None)
    
    if product:
        text = f"📦 *{product['name']}*\n\n📝 Description: {product['desc']}\n\n💰 Price: {product['price']} UAH"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add to Cart", callback_data=f"buy_{prod_id}")],
            [InlineKeyboardButton(text="⬅️ Back to List", callback_data=f"cat_{category}")]
        ])
        
        await callback.message.delete()
        
        try:
            photo_file = FSInputFile(product["photo"])
            await callback.message.answer_photo(
                photo=photo_file,
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error loading local image {product['photo']}: {e}")
            await callback.message.answer(
                text=f"⚠️ {text}\n\n_(Image could not be loaded)_",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def add_to_cart(callback: CallbackQuery):
    prod_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user_carts.setdefault(user_id, []).append(prod_id)
    await callback.answer("✅ Added to cart!")


@router.callback_query(F.data == "open_cart")
async def view_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await callback.message.edit_text(
            "🛒 Your cart is currently empty!", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍️ Open Catalog", callback_data="open_catalog")],
                [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
            ])
        )
        await callback.answer()
        return

    cart_text = "🛒 *Your Cart:*\n\n"
    total_price = 0
    
    all_products = []
    for category in PRODUCTS:
        all_products.extend(PRODUCTS[category])
        
    for prod in all_products:
        count = cart.count(prod["id"])
        if count > 0:
            item_sum = prod["price"] * count
            total_price += item_sum
            cart_text += f"▪️ {prod['name']} x{count} — {item_sum} UAH\n"
                
    cart_text += f"\n💵 *Total Price:* {total_price} UAH"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Checkout", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑️ Clear Cart", callback_data="clear_cart")],
        [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(cart_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    user_carts[callback.from_user.id] = []
    await callback.answer("🗑️ Cart cleared!")
    await view_cart(callback)


@router.callback_query(F.data == "checkout")
async def checkout_order(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await callback.answer("❌ Your cart is empty!", show_alert=True)
        return

    await state.set_state(OrderProcess.waiting_for_name)
    await callback.message.answer("📝 Step 1/3: Enter your First and Last Name:")
    await callback.message.delete()
    await callback.answer()


@router.message(OrderProcess.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if len(text.split()) < 2:
        await message.answer(
            "❌ *Invalid format!*\n"
            "Please enter both your *First Name* and *Last Name* (e.g., John Doe):",
            parse_mode="Markdown"
        )
        return

    await state.update_data(customer_name=text)
    await state.set_state(OrderProcess.waiting_for_phone)
    await message.answer("📱 *Step 2/3:* Enter your phone number (e.g., +380XXXXXXXXX):", parse_mode="Markdown")


@router.message(OrderProcess.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    text = message.text.strip()
    
    cleaned_phone = "".join(c for c in text if c.isdigit() or c == "+")
    
    digits_only = "".join(c for c in cleaned_phone if c.isdigit())
    
    if not (9 <= len(digits_only) <= 13):
        await message.answer(
            "❌ *Invalid phone number!*\n"
            "Please enter a valid phone number containing 9 to 13 digits:",
            parse_mode="Markdown"
        )
        return

    await state.update_data(customer_phone=cleaned_phone)
    await state.set_state(OrderProcess.waiting_for_delivery)
    await message.answer("🚚 *Step 3/3:* Enter your City and Cargo Office number:", parse_mode="Markdown")


@router.message(OrderProcess.waiting_for_delivery)
async def process_delivery(message: Message, state: FSMContext):
    global total_orders_count
    
    await state.update_data(customer_delivery=message.text)
    user_data = await state.get_data()
    
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "No username"
    cart = user_carts.get(user_id, [])
    admin_id = int(os.getenv("ADMIN_ID", 0))
    
    order_text = f"🔔 *NEW ORDER RECEIVED!*\n\n"
    order_text += f"👤 *Customer:* {user_data['customer_name']} ({username})\n"
    order_text += f"📱 *Phone:* `{user_data['customer_phone']}`\n"
    order_text += f"🚚 *Delivery:* {user_data['customer_delivery']}\n"
    order_text += f"🆔 *ID:* `{user_id}`\n\n"
    order_text += "📦 *Items:*\n"
    
    total_price = 0
    for category in PRODUCTS:
        for prod in PRODUCTS[category]:
            count = cart.count(prod["id"])
            if count > 0:
                item_sum = prod["price"] * count
                total_price += item_sum
                order_text += f"▪️ {prod['name']} x{count} — {item_sum} UAH\n"
                
    order_text += f"\n💵 *Total Order Amount:* {total_price} UAH"

    if admin_id != 0:
        try:
            await message.bot.send_message(chat_id=admin_id, text=order_text, parse_mode="Markdown")
            total_orders_count += 1
            logging.info(f"Order successfully sent to admin (ID: {admin_id}). Total orders: {total_orders_count}")
        except Exception as e:
            logging.error(f"Failed to send order to admin: {e}")

    user_carts[user_id] = []
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ To Main Menu", callback_data="back_to_main")]
    ])
    await message.answer("🎉 *Order successfully placed!*", reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Catalog", callback_data="open_catalog")],
        [InlineKeyboardButton(text="🛒 My Cart", callback_data="open_cart")]
    ])
    await callback.message.edit_text(
        f"👋 Hello, {callback.from_user.first_name}!\nWelcome to our Telegram Shop.", 
        reply_markup=keyboard
    )
    await callback.answer()