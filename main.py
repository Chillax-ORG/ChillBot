import logging
import os
from typing import List

import discord
from discord.commands import Option
from dotenv import load_dotenv

from dbutils import load_db, save_db
from faq_manager import FAQManager

load_dotenv()


def get_log_level(log_level_str: str) -> int:
    """Convert string log level to logging module constant."""
    log_level_str = log_level_str.upper()
    logging_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return logging_levels.get(log_level_str, logging.INFO)


log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_level = get_log_level(log_level_str)

logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = discord.Bot(intents=intents)
faq_manager = FAQManager()


@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    faq_manager.load_from_json()
    logging.info('Finished computing embeddings')


def should_ignore_message(message: discord.Message) -> bool:
    if 'https://chillax-org.github.io/chillaxdocs' in message.content or 'https://chillax.inmoresentum.net' in message.content:
        # Ignore message if it contains a link to the docs
        return True

    return False


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if should_ignore_message(message):
        return
    db = load_db(message.guild)
    if db['enabled_channel'] != message.channel.id:
        return

    answer = faq_manager.get_answer(message.content)
    if answer:
        logging.info(
            f'responding to {message.author} ({message.author.id})\nmessage: "{message.content}"\nresponse: "{answer}"')
        await message.reply(answer)


@bot.slash_command(name='enable', description='Enable automatic FAQ replies')
@discord.default_permissions(administrator=True)
async def enable(ctx: discord.ApplicationContext, channel: discord.TextChannel):
    db = load_db(ctx.guild)
    if db['enabled_channel'] == channel.id:
        await ctx.respond(f'FAQ replies already enabled for #{channel.name}', ephemeral=True)
    else:
        db['enabled_channel'] = channel.id
        save_db(ctx.guild, db)
        await ctx.respond(f'FAQ replies enabled for #{channel.name}', ephemeral=True)


@bot.slash_command(name='disable', description='Disable automatic FAQ replies')
@discord.default_permissions(administrator=True)
async def disable(ctx: discord.ApplicationContext):
    db = load_db(ctx.guild)
    if db['enabled_channel'] == -1:
        await ctx.respond('FAQ replies already disabled', ephemeral=True)
    else:
        db['enabled_channel'] = -1
        save_db(ctx.guild, db)
        await ctx.respond('FAQ replies disabled', ephemeral=True)


@bot.slash_command(name='add_faq', description='Add a new FAQ entry')
@discord.default_permissions(administrator=True)
async def add_faq(ctx: discord.ApplicationContext, question: str, answer: str):
    if faq_manager.add_entry(question, answer):
        faq_manager.save_to_json()
        await ctx.respond(f'FAQ entry added successfully: "{question}"', ephemeral=True)
    else:
        await ctx.respond(f'FAQ entry already exists: "{question}"', ephemeral=True)


async def get_faq_questions(ctx: discord.AutocompleteContext) -> List[str]:
    return [entry['question'] for entry in faq_manager.faq_entries if ctx.value.lower() in entry['question'].lower()]


@bot.slash_command(name='update_faq', description='Update an existing FAQ entry')
@discord.default_permissions(administrator=True)
async def update_faq(
    ctx: discord.ApplicationContext,
    question: Option(str, "The question to update", autocomplete=get_faq_questions),
    new_answer: str
):
    if faq_manager.update_entry(question, new_answer):
        faq_manager.save_to_json()
        await ctx.respond(f'FAQ entry updated successfully: "{question}"', ephemeral=True)
    else:
        await ctx.respond(f'FAQ entry not found: "{question}"', ephemeral=True)


@bot.slash_command(name='remove_faq', description='Remove an FAQ entry')
@discord.default_permissions(administrator=True)
async def remove_faq(
    ctx: discord.ApplicationContext,
    question: Option(str, "The question to remove", autocomplete=get_faq_questions)
):
    if faq_manager.remove_entry(question):
        faq_manager.save_to_json()
        await ctx.respond(f'FAQ entry removed successfully: "{question}"', ephemeral=True)
    else:
        await ctx.respond(f'FAQ entry not found: "{question}"', ephemeral=True)


@bot.slash_command(name='list_faq', description='Return all FAQ entries as JSON file')
@discord.default_permissions(administrator=True)
async def list_faq(ctx: discord.ApplicationContext):
    if not os.path.exists(faq_manager.faq_filename):
        await ctx.respond('No FAQ entries found.', ephemeral=True)
        return

    discord_file = discord.File(faq_manager.faq_filename)

    await ctx.respond("Here are the FAQ entries:", file=discord_file, ephemeral=True)


bot.run(TOKEN)
