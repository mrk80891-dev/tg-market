import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8951367573:AAEiRaHX_MbRYNca85G9Z1EUmsuSasaN5zc"
ADMIN_ID = 8605504295

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

MODERATION_QUEUE = {}
MARKET_ITEMS = []

class SellState(StatesGroup):
    waiting_for_title = State()
    waiting_for_price = State()

def main_menu(user_id):
    keyboard = [
        [InlineKeyboardButton(text="🛍 Купить товар", callback_data="buy_menu")],
        [InlineKeyboardButton(text="➕ Продать товар", callback_data="sell_item")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(text="👑 Админ-панель (Заявки)", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "<b>🔥 Здарова, бро! Добро пожаловать на Маркет.</b>\n\n"
        "Выставляй товары или покупай нужное. Всё через админа!",
        reply_markup=main_menu(message.from_user.id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    await callback.message.edit_text("<b>Главное меню:</b>", reply_markup=main_menu(callback.from_user.id), parse_mode="HTML")

@dp.callback_query(F.data == "sell_item")
async def sell_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Опиши свой товар:", parse_mode="HTML")
    await state.set_state(SellState.waiting_for_title)
    await callback.answer()

@dp.message(SellState.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Укажи цену (например: 100 руб или 50 звезд):", parse_mode="HTML")
    await state.set_state(SellState.waiting_for_price)

@dp.message(SellState.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    data = await state.get_data()
    item_id = str(len(MODERATION_QUEUE) + len(MARKET_ITEMS) + 1)
    
    item = {
        "id": item_id,
        "seller_id": message.from_user.id,
        "seller_username": message.from_user.username or "скрыт",
        "title": data['title'],
        "price": message.text
    }
    MODERATION_QUEUE[item_id] = item
    await state.clear()
    
    await message.answer("✅ Заявка отправлена администратору на проверку!", reply_markup=main_menu(message.from_user.id))
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 Заявка #ID {item_id}\n👤 От: @{item['seller_username']}\n📦 Товар: {item['title']}\n💰 Цена: {item['price']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_yes_{item_id}"),
                 InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{item_id}")]
            ])
        )
    except: pass

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    if not MODERATION_QUEUE:
        await callback.message.edit_text("👑 Нет заявок.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]]))
        return
    
    keyboard = [[InlineKeyboardButton(text=f"📦 {item['title']} ({item['price']})", callback_data=f"adm_view_{item_id}")] for item_id, item in MODERATION_QUEUE.items()]
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")])
    await callback.message.edit_text("👑 Заявки на модерацию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("adm_view_"))
asyncdef admin_view(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    item_id = callback.data.split("_")[2]
    item = MODERATION_QUEUE.get(item_id)
    if not item: return await callback.answer("Уже обработано!")
    
    await callback.message.edit_text(
        f"📦 Товар #{item_id}\nПродавец: @{item['seller_username']}\nТовар: {item['title']}\nЦена: {item['price']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_yes_{item_id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_no_{item_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
        ])
    )

@dp.callback_query(F.data.startswith("adm_yes_"))
async def adm_yes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    item_id = callback.data.split("_")[2]
    item = MODERATION_QUEUE.pop(item_id, None)
    if item:
        MARKET_ITEMS.append(item)
        await callback.message.edit_text(f"✅ Товар #{item_id} одобрен!")
        try: await bot.send_message(item['seller_id'], f"🎉 Твой товар «{item['title']}» выставлен на маркет!")
        except: pass

@dp.callback_query(F.data.startswith("adm_no_"))
async def adm_no(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    item_id = callback.data.split("_")[2]
    item = MODERATION_QUEUE.pop(item_id, None)
    if item:
        await callback.message.edit_text(f"❌ Товар #{item_id} отклонен.")
        try: await bot.send_message(item['seller_id'], f"❌ Твой товар отклонен.")
        except: pass

@dp.callback_query(F.data == "buy_menu")
async def buy_menu(callback: CallbackQuery):
    if not MARKET_ITEMS:
        await callback.message.edit_text("😔 Товаров пока нет.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]]))
        return
    keyboard = [[InlineKeyboardButton(text=f"🛒 {item['title']} — {item['price']}", callback_data=f"buy_{i}")] for i, item in enumerate(MARKET_ITEMS)]
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")])
    await callback.message.edit_text("🛍 Витрина:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery):
    item = MARKET_ITEMS[int(callback.data.split("_")[1])]
    await callback.message.edit_text(
        f"🛒 Покупка: {item['title']}\nЦена: {item['price']}\n\nСвяжись с админом для оплаты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать админу", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_menu")]
        ])
    )

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.message.edit_text(f"👤 Твой ID: <code>{callback.from_user.id}</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]]))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
