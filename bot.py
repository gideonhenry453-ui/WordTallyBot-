import os
import re
import io
import asyncio
from datetime import datetime
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

# User sessions
user_sessions = {}

# ==================== TEXT ANALYSIS FUNCTIONS ====================
def count_words(text):
    """Count total words"""
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def count_chars(text):
    """Count characters (with and without spaces)"""
    return {
        "with_spaces": len(text),
        "without_spaces": len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    }

def count_sentences(text):
    """Count sentences"""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def count_paragraphs(text):
    """Count paragraphs"""
    paragraphs = [p for p in text.split('\n') if p.strip()]
    return len(paragraphs)

def count_lines(text):
    """Count lines"""
    lines = text.split('\n')
    return len([l for l in lines if l.strip()])

def count_unique_words(text):
    """Count unique words"""
    words = re.findall(r'\b\w+\b', text.lower())
    return len(set(words))

def word_frequency(text):
    """Get word frequency"""
    words = re.findall(r'\b\w+\b', text.lower())
    return Counter(words).most_common(10)

def count_characters_by_type(text):
    """Count character types"""
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    spaces = sum(1 for c in text if c.isspace())
    special = len(text) - letters - digits - spaces
    return {
        "letters": letters,
        "digits": digits,
        "spaces": spaces,
        "special": special
    }

def calculate_readability(text):
    """Calculate basic readability scores"""
    words = count_words(text)
    sentences = count_sentences(text)
    chars = count_chars(text)["without_spaces"]
    
    if words == 0 or sentences == 0:
        return {"score": 0, "level": "No text to analyze"}
    
    # Average words per sentence
    avg_words = words / sentences if sentences > 0 else 0
    
    # Flesch Reading Ease (simplified)
    if chars > 0:
        flesch = 206.835 - 1.015 * (words / sentences) - 84.6 * (chars / words)
    else:
        flesch = 0
    
    # Determine reading level
    if flesch >= 90:
        level = "Very Easy (5th grade)"
    elif flesch >= 80:
        level = "Easy (6th grade)"
    elif flesch >= 70:
        level = "Fairly Easy (7th grade)"
    elif flesch >= 60:
        level = "Plain English (8th-9th grade)"
    elif flesch >= 50:
        level = "Fairly Difficult (10th-12th grade)"
    elif flesch >= 30:
        level = "Difficult (College)"
    else:
        level = "Very Difficult (College Graduate)"
    
    return {
        "score": flesch,
        "level": level,
        "avg_words": avg_words
    }

def estimate_reading_time(text):
    """Estimate reading time"""
    words = count_words(text)
    # Average reading speed: 200-250 words per minute
    reading_speed = 225  # words per minute
    minutes = words / reading_speed
    seconds = minutes * 60
    return {
        "minutes": minutes,
        "seconds": seconds
    }

# ==================== KEYBOARD FUNCTIONS ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Full Analysis", callback_data="full")],
        [InlineKeyboardButton("📝 Word Frequency", callback_data="frequency")],
        [InlineKeyboardButton("📖 Readability", callback_data="readability")],
        [InlineKeyboardButton("📋 Stats Summary", callback_data="summary")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_result_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Full Analysis", callback_data="full")],
        [InlineKeyboardButton("📝 Word Frequency", callback_data="frequency")],
        [InlineKeyboardButton("📖 Readability", callback_data="readability")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Initialize user session
    user_id = str(user.id)
    user_sessions[user_id] = {}
    
    welcome_message = (
        f"📝 Welcome {user.first_name} to **WordTallyBot**!\n\n"
        "Your complete text analysis companion!\n\n"
        "**✨ Features:**\n"
        "• 📊 Count words, characters, sentences, paragraphs\n"
        "• 📝 Analyze word frequency\n"
        "• 📖 Calculate readability scores\n"
        "• ⏱️ Estimate reading time\n"
        "• 📋 Detailed text statistics\n\n"
        "**🎯 How to use:**\n"
        "• Send me any text\n"
        "• Click the buttons for detailed analysis\n"
        "• Get instant statistics!\n\n"
        "⬇️ Send me text or use the buttons below!"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📖 **WordTallyBot User Guide**\n\n"
        "**📊 Full Analysis**\n"
        "• Shows all statistics at once\n"
        "• Words, characters, sentences, paragraphs\n\n"
        "**📝 Word Frequency**\n"
        "• Shows most common words\n"
        "• Top 10 words with counts\n\n"
        "**📖 Readability**\n"
        "• Flesch Reading Ease score\n"
        "• Reading level\n"
        "• Average words per sentence\n\n"
        "**📋 Stats Summary**\n"
        "• Quick overview of key metrics\n"
        "• Characters, words, sentences\n\n"
        "**⏱️ Reading Time**\n"
        "• Estimated reading time\n"
        "• Based on average reading speed\n\n"
        "**Commands**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - Get quick stats\n"
        "/frequency - Get word frequency"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    text = " ".join(context.args) if context.args else None
    
    if not text:
        await update.message.reply_text(
            "📝 **Please send text to analyze**\n\n"
            "Example: `/stats The quick brown fox jumps over the lazy dog`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    result = analyze_text(text)
    await update.message.reply_text(
        result,
        parse_mode="Markdown",
        reply_markup=get_result_keyboard()
    )

async def frequency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /frequency command"""
    text = " ".join(context.args) if context.args else None
    
    if not text:
        await update.message.reply_text(
            "📝 **Please send text to analyze**\n\n"
            "Example: `/frequency The quick brown fox jumps over the lazy dog`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    result = analyze_frequency(text)
    await update.message.reply_text(
        result,
        parse_mode="Markdown",
        reply_markup=get_result_keyboard()
    )

# ==================== ANALYSIS FUNCTIONS ====================
def analyze_text(text):
    """Perform full text analysis"""
    word_count = count_words(text)
    char_counts = count_chars(text)
    sentence_count = count_sentences(text)
    paragraph_count = count_paragraphs(text)
    line_count = count_lines(text)
    unique_words = count_unique_words(text)
    reading_time = estimate_reading_time(text)
    readability = calculate_readability(text)
    char_types = count_characters_by_type(text)
    
    result = (
        f"📊 **Text Analysis Report**\n\n"
        f"📝 **Words:** {word_count}\n"
        f"🔤 **Characters:**\n"
        f"  • With spaces: {char_counts['with_spaces']}\n"
        f"  • Without spaces: {char_counts['without_spaces']}\n"
        f"📖 **Sentences:** {sentence_count}\n"
        f"📄 **Paragraphs:** {paragraph_count}\n"
        f"📏 **Lines:** {line_count}\n"
        f"🔄 **Unique Words:** {unique_words}\n\n"
        f"📊 **Character Types:**\n"
        f"  • Letters: {char_types['letters']}\n"
        f"  • Digits: {char_types['digits']}\n"
        f"  • Spaces: {char_types['spaces']}\n"
        f"  • Special: {char_types['special']}\n\n"
        f"⏱️ **Reading Time:** {reading_time['minutes']:.1f} min ({reading_time['seconds']:.0f} sec)\n"
        f"📖 **Readability:** {readability['score']:.1f} ({readability['level']})\n"
        f"📊 **Avg Words/Sentence:** {readability['avg_words']:.1f}"
    )
    
    return result

def analyze_frequency(text):
    """Analyze word frequency"""
    frequency = word_frequency(text)
    
    if not frequency:
        return "📝 **No words found to analyze**"
    
    result = "📝 **Word Frequency (Top 10)**\n\n"
    for i, (word, count) in enumerate(frequency, 1):
        result += f"{i}. **{word}** - {count} time{'s' if count > 1 else ''}\n"
    
    return result

def analyze_summary(text):
    """Quick summary analysis"""
    word_count = count_words(text)
    char_counts = count_chars(text)
    sentence_count = count_sentences(text)
    reading_time = estimate_reading_time(text)
    
    result = (
        f"📋 **Quick Summary**\n\n"
        f"📝 Words: {word_count}\n"
        f"🔤 Characters: {char_counts['without_spaces']}\n"
        f"📖 Sentences: {sentence_count}\n"
        f"⏱️ Reading Time: {reading_time['minutes']:.1f} min\n\n"
        f"💡 For full analysis, click 'Full Analysis' below."
    )
    
    return result

def analyze_readability(text):
    """Detailed readability analysis"""
    readability = calculate_readability(text)
    word_count = count_words(text)
    sentence_count = count_sentences(text)
    char_count = count_chars(text)["without_spaces"]
    
    if word_count == 0:
        return "📖 **No text to analyze for readability**"
    
    result = (
        f"📖 **Readability Analysis**\n\n"
        f"📊 **Flesch Reading Ease:** {readability['score']:.1f}\n"
        f"📚 **Reading Level:** {readability['level']}\n"
        f"📝 **Avg Words/Sentence:** {readability['avg_words']:.1f}\n\n"
        f"📊 **Metrics:**\n"
        f"  • Total Words: {word_count}\n"
        f"  • Total Sentences: {sentence_count}\n"
        f"  • Characters (no spaces): {char_count}\n\n"
        f"💡 **Flesch Score Guide:**\n"
        f"  • 90-100: Very Easy\n"
        f"  • 60-70: Plain English\n"
        f"  • 30-50: Difficult\n"
        f"  • 0-30: Very Difficult"
    )
    
    return result

# ==================== CALLBACK HANDLERS ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = str(update.effective_user.id)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    # Get the last analyzed text
    last_text = user_sessions.get(user_id, {}).get("last_text", "")
    
    if data == "full":
        if not last_text:
            await query.edit_message_text(
                "📝 **Send me text to analyze first!**\n\n"
                "Please send any text and then use the buttons.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        result = analyze_text(last_text)
        await query.edit_message_text(
            result,
            parse_mode="Markdown",
            reply_markup=get_result_keyboard()
        )
    
    elif data == "frequency":
        if not last_text:
            await query.edit_message_text(
                "📝 **Send me text to analyze first!**\n\n"
                "Please send any text and then use the buttons.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        result = analyze_frequency(last_text)
        await query.edit_message_text(
            result,
            parse_mode="Markdown",
            reply_markup=get_result_keyboard()
        )
    
    elif data == "readability":
        if not last_text:
            await query.edit_message_text(
                "📝 **Send me text to analyze first!**\n\n"
                "Please send any text and then use the buttons.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        result = analyze_readability(last_text)
        await query.edit_message_text(
            result,
            parse_mode="Markdown",
            reply_markup=get_result_keyboard()
        )
    
    elif data == "summary":
        if not last_text:
            await query.edit_message_text(
                "📝 **Send me text to analyze first!**\n\n"
                "Please send any text and then use the buttons.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        result = analyze_summary(last_text)
        await query.edit_message_text(
            result,
            parse_mode="Markdown",
            reply_markup=get_result_keyboard()
        )
    
    elif data == "help":
        await help_command(update, context)
    
    elif data == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "Send me text to analyze or use the buttons above!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MESSAGE HANDLERS ====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Store the text for later analysis
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id]["last_text"] = text
    
    # Perform automatic analysis
    word_count = count_words(text)
    char_counts = count_chars(text)
    sentence_count = count_sentences(text)
    reading_time = estimate_reading_time(text)
    
    # Send quick summary
    await update.message.reply_text(
        f"📝 **Text Received!**\n\n"
        f"📊 Quick Stats:\n"
        f"• Words: {word_count}\n"
        f"• Characters: {char_counts['without_spaces']}\n"
        f"• Sentences: {sentence_count}\n"
        f"• Reading Time: {reading_time['minutes']:.1f} min\n\n"
        f"💡 Click below for detailed analysis!",
        parse_mode="Markdown",
        reply_markup=get_result_keyboard()
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document messages (text files)"""
    document = update.message.document
    
    # Check if it's a text file
    if document.mime_type and document.mime_type.startswith("text/"):
        try:
            file = await document.get_file()
            content = await file.download_as_bytearray()
            text = content.decode('utf-8')
            
            user_id = str(update.effective_user.id)
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]["last_text"] = text
            
            # Perform analysis
            word_count = count_words(text)
            char_counts = count_chars(text)
            sentence_count = count_sentences(text)
            reading_time = estimate_reading_time(text)
            
            await update.message.reply_text(
                f"📄 **Document Received!**\n\n"
                f"📊 Quick Stats:\n"
                f"• Words: {word_count}\n"
                f"• Characters: {char_counts['without_spaces']}\n"
                f"• Sentences: {sentence_count}\n"
                f"• Reading Time: {reading_time['minutes']:.1f} min\n\n"
                f"💡 Click below for detailed analysis!",
                parse_mode="Markdown",
                reply_markup=get_result_keyboard()
            )
        except Exception as e:
            print(f"Document error: {e}")
            await update.message.reply_text(
                "❌ **Error reading document**\n\n"
                "Please make sure it's a valid text file.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    else:
        await update.message.reply_text(
            "📄 **Unsupported document type**\n\n"
            "Please send a .txt file for analysis.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    print("📝 Starting WordTallyBot...")
    print("📊 Ready to analyze text!")
    
    # Build application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .build()
    )
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("frequency", frequency_command))
    
    # Add callback handler for buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Start the bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
