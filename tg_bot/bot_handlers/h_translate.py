from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from tg_bot.states import Translate
import tg_bot.tg_keyboards as tgk
from tg_bot.utils import get_item, handle_translate

router = Router()

async def process_translation(user_id: int, message: Message, state: FSMContext):
    word_data = await state.get_data()
    word_data["user_id"] = str(user_id)

    msg = await message.answer("⏳ Перевожу...")

    try:
        translate = handle_translate(word_data)
    except Exception:
        await msg.delete()
        await message.answer(
            "Не удалось получить перевод 😔 Пожалуйста, попробуйте еще раз.",
            reply_markup=tgk.back_to_menu_ikb()
        )
        await state.clear()
        return

    word = word_data.get("word")
    context = word_data.get("context")
    translation = translate.get("translation", "")

    # Сохраняем все детали перевода в словарь состояния FSM
    await state.update_data(
        transcription=translate.get("transcription", ""),
        explanation=translate.get("explanation", ""),
        examples=translate.get("examples", [])
    )

    if context:
        answer = f"🇬🇧 <b>{word}</b> <i>(в контексте: \"{context}\")</i>\n\n📝 <b>Перевод:</b> {translation}"
    else:
        answer = f"🇬🇧 <b>{word}</b>\n\n📝 <b>Перевод:</b> {translation}"

    await msg.delete()
    
    # Фиксируем состояние показа результатов
    await state.set_state(Translate.showing_result)

    await message.answer(
        answer,
        reply_markup=tgk.get_translation_details_ikb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "translate")
@router.callback_query(F.data == "translate_new")
async def enter_translate(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer(
        "✍️ <b>Введите слово или фразу, которую хотите перевести:</b>",
        reply_markup=tgk.back_to_menu_ikb(),
        parse_mode="HTML"
    )
    await state.set_state(Translate.passing_word)


@router.message(Translate.passing_word)
async def get_word(message: Message, state: FSMContext):
    word = get_item(message=message, entity="clean_text")

    if not word:
        await message.answer(
            "Я не смог распознать текст 🧐 Пожалуйста, введите корректное слово:",
            reply_markup=tgk.back_to_menu_ikb()
        )
        return

    await state.update_data(word=word)
    await state.set_state(Translate.passing_context)
    
    # Кнопка пропуска контекста или отмены
    await message.answer(
        "Отлично! ✅\nТеперь введите контекст (предложение, где встречается слово), чтобы перевод был точнее, или пропустите этот шаг:",
        reply_markup=tgk.get_context_ikb()
    )


@router.message(Translate.passing_context)
async def get_context(message: Message, state: FSMContext):
    context = get_item(message=message, entity="clean_text")

    if not context:
        await message.answer(
            "Текст контекста содержит недопустимые символы 🧐 Попробуйте еще раз:",
            reply_markup=tgk.get_context_ikb()
        )
        return

    await state.update_data(context=context)
    await process_translation(user_id=message.from_user.id, message=message, state=state)


@router.callback_query(StateFilter(Translate.passing_context), F.data == "pass_context")
async def pass_context(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(context=None)
    await process_translation(user_id=call.from_user.id, message=call.message, state=state)

# ==========================================
# ПОП-АПЫ ДЕТАЛЕЙ (ЧТЕНИЕ ИЗ FSM STATE)
# ==========================================

@router.callback_query(StateFilter(Translate.showing_result), F.data == "show_transcription")
async def show_transcription(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    word = data.get("word", "")
    tr = data.get("transcription")

    if tr:
        await call.answer(f"🗣 Транскрипция '{word}':\n\n[{tr}]", show_alert=True)
    else:
        await call.answer("🗣 Транскрипция для этого слова недоступна.", show_alert=True)


@router.callback_query(StateFilter(Translate.showing_result), F.data == "show_explanation")
async def show_explanation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    word = data.get("word", "")
    exp = data.get("explanation")

    if exp:
        await call.answer(f"💡 Объяснение '{word}':\n\n{exp}", show_alert=True)
    else:
        await call.answer("💡 Объяснение для этого слова недоступно.", show_alert=True)

async def send_detail_response(call: CallbackQuery, title: str, text: str):
    """Отправляет всплывающее окно для короткого текста или сообщение в чат для длинного."""
    alert_text = f"{title}\n\n{text}"
    
    # Лимит Telegram на show_alert ~200 символов
    if len(alert_text) <= 180:
        await call.answer(alert_text, show_alert=True)
    else:
        await call.answer("📄 Подробный ответ отправлен в чат")
        await call.message.answer(f"<b>{title}</b>\n\n{text}", parse_mode="HTML")        


@router.callback_query(StateFilter(Translate.showing_result), F.data == "show_examples")
async def show_examples(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    word = data.get("word", "")
    examples = data.get("examples")

    if not examples:
        await call.answer("📚 Примеры употребления недоступны.", show_alert=True)
        return

    items = []
    if isinstance(examples, dict):
        for key, val in examples.items():
            items.append(f"• {key} — {val}" if val else f"• {key}")
    elif isinstance(examples, list):
        for item in examples:
            if isinstance(item, dict):
                en = item.get("en") or item.get("original") or item.get("text") or ""
                ru = item.get("ru") or item.get("translation") or ""
                items.append(f"• {en} — {ru}" if en and ru else f"• {en}{ru}")
            else:
                items.append(f"• {item}")
    else:
        items.append(str(examples))

    examples_text = "\n".join(items)
    await send_detail_response(call, f"📚 Примеры с '{word}'", examples_text)
