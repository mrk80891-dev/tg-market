import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8951367573:AAEiRaHX_MbRYNca85G9Z1EUmsuSasaN5zc"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATABASE = []

class SellState(StatesGroup):
    waiting_for_title = State()
    waiting_for_price = State()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Купить товар", callback_data="buy_menu")],
        [InlineKeyboardButton(text="➕ Продать товар", callback_data="sell_item")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "<b>Здарова, бро! Это твой собственный Маркетплейс.</b>\n\n"
        "Здесь ты можешь выставить товар на продажу или купить что-то нужное.\n"
        "Комиссия сервиса: <b>15%</b>.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>Главное меню маркета:</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "sell_item")
async def sell_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Опиши свой товар (например: <i>Аккаунт Steam с праймом</i>):", parse_mode="HTML")
    await state.set_state(SellState.waiting_for_title)
    await callback.answer()

@dp.message(SellState.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь укажи цену в рублях (просто цифру, например: 500):")
    await state.set_state(SellState.waiting_for_price)

@dp.message(SellState.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Брат, введи цену цифрами!")
        return
    
    price = int(message.text)
    data = await state.get_data()
    title = data['title']
    
    item = {
        "seller": message.from_user.id,
        "title": title,
        "price": price
    }
    DATABASE.append(item)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Товар успешно выставлен на маркет!</b>\n\n"
        f"📦 Товар: {title}\n"
        f"💰 Цена: {price} руб.\n\n"
        f"Как только его купят, 85% уйдет тебе, а 15% — комиссия маркета.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "buy_menu")
async def buy_menu(callback: CallbackQuery):
    if not DATABASE:
        await callback.message.edit_text(
            "😔 На маркете пока нет товаров.\nБудь первыми, выстави что-нибудь на продажу!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return
    
    keyboard = []
    for index, item in enumerate(DATABASE):
        keyboard.append([InlineKeyboardButton(text=f"🛒 {item['title']} — {item['price']} руб.", callback_data=f"buy_{index}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")])
    
    await callback.message.edit_text("<b>Доступные товары на маркете:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    item = DATABASE[index]
    
    price = item['price']
    commission = int(price * 0.15)
    seller_gets = price - commission
    
    await callback.message.answer(
        f"🎉 <b>Покупка прошла успешно!</b>\n\n"
   f"Ты купил: {item['title']}\n"
        f"Цена: {price} руб.\n"
        f"*(В реале списались бабки, продавец получил {seller_gets} руб., а система забрала комиссия {commission} руб.)*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    DATABASE.pop(index)
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile_view(callback: CallbackQuery):
    await callback.message.edit_text(
        f"👤 <b>Твой профиль</b>\n\nID: <code>{callback.from_user.id}</code>\nБаланс: 0 руб.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
