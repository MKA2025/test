from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Main menu keyboard
main_menu_keyboard = [
    [
        InlineKeyboardButton("Quality Settings", callback_data='menu_quality'),
        InlineKeyboardButton("Format Settings", callback_data='menu_format')
    ],
    [
        InlineKeyboardButton("Current Settings", callback_data='menu_settings'),
        InlineKeyboardButton("Help", callback_data='menu_help')
    ]
]

# Quality selection keyboard
quality_keyboard = [
    [
        InlineKeyboardButton("Master (MQA)", callback_data='quality_mqa'),
        InlineKeyboardButton("HiFi", callback_data='quality_hifi')
    ],
    [
        InlineKeyboardButton("High", callback_data='quality_high'),
        InlineKeyboardButton("Medium", callback_data='quality_medium')
    ],
    [
        InlineKeyboardButton("Low", callback_data='quality_low'),
        InlineKeyboardButton("Back", callback_data='menu_main')
    ]
]

# Format selection keyboard
format_keyboard = [
    [
        InlineKeyboardButton("Dolby Atmos", callback_data='format_atmos'),
        InlineKeyboardButton("Sony 360", callback_data='format_360')
    ],
    [
        InlineKeyboardButton("FLAC", callback_data='format_flac'),
        InlineKeyboardButton("AAC", callback_data='format_aac')
    ],
    [
        InlineKeyboardButton("MP3", callback_data='format_mp3'),
        InlineKeyboardButton("Back", callback_data='menu_main')
    ]
]
