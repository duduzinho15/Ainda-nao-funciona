"""
Utility functions for safely handling Telegram message operations.
"""
from typing import Optional, Any, Union, Dict, List
from telegram import Update, Message
from telegram.constants import ParseMode
import logging

logger = logging.getLogger('garimpeiro_bot.message_utils')

def safe_reply_text(update: Optional[Update], text: str, **kwargs) -> Optional[Message]:
    """
    Safely send a reply to a message, handling cases where update or message might be None.
    
    Args:
        update: The Telegram update object
        text: The text to send
        **kwargs: Additional arguments to pass to reply_text
        
    Returns:
        The sent Message object, or None if the message couldn't be sent
    """
    if not update or not update.effective_message:
        logger.warning("Cannot send message: update or effective_message is None")
        return None
        
    try:
        return update.effective_message.reply_text(text, **kwargs)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def safe_edit_message_text(
    context: Any, 
    chat_id: Optional[Union[int, str]] = None, 
    message_id: Optional[int] = None,
    text: Optional[str] = None,
    **kwargs
) -> Optional[Message]:
    """
    Safely edit a message, handling cases where context or message_id might be None.
    
    Args:
        context: The callback context
        chat_id: The chat ID
        message_id: The message ID to edit
        text: The new text
        **kwargs: Additional arguments to pass to edit_message_text
        
    Returns:
        The edited Message object, or None if the message couldn't be edited
    """
    if not context or not hasattr(context, 'bot') or not context.bot:
        logger.warning("Cannot edit message: context or bot is invalid")
        return None
        
    if chat_id is None or message_id is None or text is None:
        logger.warning("Cannot edit message: missing required parameters")
        return None
        
    try:
        return context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return None

def safe_delete_message(context: Any, chat_id: Optional[Union[int, str]] = None, message_id: Optional[int] = None) -> bool:
    """
    Safely delete a message, handling cases where context or message_id might be None.
    
    Args:
        context: The callback context
        chat_id: The chat ID
        message_id: The message ID to delete
        
    Returns:
        bool: True if the message was deleted, False otherwise
    """
    if not context or not hasattr(context, 'bot') or not context.bot:
        logger.warning("Cannot delete message: context or bot is invalid")
        return False
        
    if chat_id is None or message_id is None:
        logger.warning("Cannot delete message: missing required parameters")
        return False
        
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        return False
