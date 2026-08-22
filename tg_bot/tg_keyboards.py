from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Меню для неавторизованного пользователя (Гостя)
def get_auth_choice_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Войти", callback_data="auth_start")
    builder.button(text="📝 Зарегистрироваться", callback_data="reg_start")
    builder.adjust(1) # Кнопки друг под другом для лучшего UX
    return builder.as_markup()

# Главное меню для авторизованного пользователя
def get_main_menu_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Переводчик", callback_data="translate")
    builder.adjust(1)
    return builder.as_markup()

# Инлайн-кнопка отмены для FSM-шагов
def get_cancel_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить", callback_data="cancel_action")
    return builder.as_markup()

# Клавиатура со свежим callback для кнопки "Назад"
def get_step_ikb(back_callback: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if back_callback:
        builder.button(text="⬅️ Назад", callback_data=back_callback)
        
    builder.button(text="❌ Отменить", callback_data="cancel_action")
    builder.adjust(2)
    return builder.as_markup()

# Кнопка возврата в меню / отмены
def back_to_menu_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить", callback_data="cancel_action")
    return builder.as_markup()

# Клавиатура на шаге ввода контекста
def get_context_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏩ Пропустить контекст", callback_data="pass_context")
    builder.button(text="❌ Отменить", callback_data="cancel_action")
    builder.adjust(1)
    return builder.as_markup()

# Клавиатура к результату перевода
def get_translation_details_ikb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Кнопки детализации с простыми callback_data
    builder.button(text="🗣 Транскрипция", callback_data="show_transcription")
    builder.button(text="💡 Объяснение", callback_data="show_explanation")
    builder.button(text="📚 Примеры", callback_data="show_examples")
    
    # Кнопки навигации
    builder.button(text="🔄 Перевести ещё", callback_data="translate_new")
    builder.button(text="🏠 В главное меню", callback_data="cancel_action")
    
    builder.adjust(2, 1, 2)
    return builder.as_markup()