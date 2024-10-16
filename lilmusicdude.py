import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.utils import get
from yt_dlp import YoutubeDL


import time

# Import disc token from env
load_dotenv('environment/lilmusicdude.env')
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='$', intents=intents)

# Setup YDL parameters
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
ydl = YoutubeDL(YDL_OPTIONS)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

voice = None
songQueue = []
songName = None

def checkQueue():
    if len(songQueue) > 0:
        playFromDownloadedURL(songQueue.pop(0))

def playFromDownloadedURL(url):
    voice.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after = lambda _: checkQueue())
    voice.source = PCMVolumeTransformer(voice.source, .03)
    voice.is_playing()

def getURL(url):
    with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
    return info['url']

# Add bot to voice channel
@bot.command(name = "start", aliases = ['s'])
async def start(ctx):
    global voice
    if voice is None:
        voice = await ctx.author.voice.channel.connect()
    else:
        await ctx.send("Already in a voice channel!")


@bot.command(name = "queue", aliases = ['q'])
async def queue(ctx, url, answer):
    if voice is None:
        await ctx.send("Not in voice channel yet!")
        return

    # Play immediately (nothing in the queue)
    if not voice.is_playing():
        global songName
        # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
        songName = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()
        playFromDownloadedURL(getURL(url))
    else:
        await ctx.send("Adding to queue!")
        songQueue.append(getURL(url))
        return

@bot.command(name = "guess", aliases = ['g'])
async def guess(ctx, answer):
    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()
    if answer == songName:
        await ctx.send("Correct answer!")


# COMMENCE!
bot.run(TOKEN)