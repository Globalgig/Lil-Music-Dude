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
songVolume = 0.3

def checkQueue():
    if len(songQueue) > 0:
        nextSong = songQueue.pop(0)
        print(nextSong[1])
        playFromDownloadedURL(nextSong[0], nextSong[1])

def playFromDownloadedURL(url, songAnswer):
    global songName
    songName = songAnswer
    voice.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after = lambda _: checkQueue())
    voice.source = PCMVolumeTransformer(voice.source, songVolume)
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

    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()

    # Play immediately (nothing in the queue)
    if not voice.is_playing(): 
        playFromDownloadedURL(getURL(url), answer)
    else:
        await ctx.send("Adding to queue!")
        songQueue.append([getURL(url), answer])
        return

@bot.command(name = "guess", aliases = ['g'])
async def guess(ctx, answer):
    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()
    if answer == songName:
        await ctx.send("Correct answer!")

@bot.command(name = "adjustVolume", alias = ['a'])
async def adjustVolume(_, volume):
    global songVolume
    songVolume = volume

# COMMENCE!
bot.run(TOKEN)