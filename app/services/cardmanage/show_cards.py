import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

import app.keyboards as kb
from app.requests import send_request
from app.middlewares.i18n_init import i18n
from app.services import handle_decks_list_request
from app.states import CardManage
from settings import BASE_URL

_ = i18n.gettext


async def process_show_cards(callback: CallbackQuery, state: FSMContext):
    """
    Processes the request to show cards in a specific deck.
    """
    await callback.answer()
    slug = callback.data.split('_')[-1]
    tg_id = state.key.user_id
    url = f'{BASE_URL}/deck/api/v1/manage/{tg_id}/{slug}/'
    response = await send_request(url, method='GET')
    status = response.get('status')

    if status == 200:
        data = response.get('data', [])
        cards_list, cards_id_index = format_cards_list(data)

        if cards_list:
            await callback.message.edit_text(cards_list, reply_markup=await kb.show_cards_action_buttons(slug))
            await state.set_state(CardManage.card_ops_state)
            await state.update_data(cards_id_index=cards_id_index, slug=slug)
        else:
            await callback.message.edit_text(
                _('deck_empty'),
                reply_markup=await kb.back_to_decklist_or_details_addcard(slug)
            )
    else:
        text = _('something_went_wrong')
        await callback.message.answer(text, reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1.5)
        await handle_decks_list_request(callback.message, state)


def format_cards_list(data):
    """
    Formats the list of cards for display and generates a mapping of card IDs to row numbers.

    Args:
        data (list): List of cards data.

    Returns:
        tuple: A tuple containing the formatted cards list string and the card ID index mapping.
    """
    cards_list = ''
    card_id_to_row_number = {}
    cur_row_number = 1
    cards_id_index = {}

    # Sort cards by card_id
    data.sort(key=lambda x: x['card_id'])

    # Build the list of card entries
    for card in data:
        card_id = card['card_id']
        if card_id not in card_id_to_row_number:
            cards_list += _('card_list_entry').format(cur_row_number, card.get("side1"), card.get("side2"))
            card_id_to_row_number[card_id] = cur_row_number
            cards_id_index[cur_row_number] = card_id
            cur_row_number += 1
        else:
            cards_list += _('card_list_entry').format(card_id_to_row_number[card_id], card.get("side1"),
                                                      card.get("side2"))
            cards_id_index[card_id_to_row_number[card_id]] = card_id

    return cards_list, cards_id_index
