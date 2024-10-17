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
songVolume = 0.03

players = []
playersQueued = []
currentSongPlayer = None

def endRound():
    global playersQueued
    playersQueued = []

def checkQueue():
    if len(songQueue) > 0:
        nextSong = songQueue.pop(0)
        playFromDownloadedURL(nextSong[0], nextSong[1])
        return

    if set(playersQueued) == set([player[0] for player in players]):
        endRound()
        return

def playFromDownloadedURL(url, songAnswer, nick):
    global songName
    songName = songAnswer
    global currentSongPlayer
    currentSongPlayer = nick
    voice.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS), after = lambda _: checkQueue())
    voice.source = PCMVolumeTransformer(voice.source, songVolume)
    voice.is_playing()

def getURL(url):
    with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
    return info['url']

# Add bot to voice channel
@bot.command(name = "begin", aliases = ['b'])
async def begin(ctx):
    global voice
    if voice is None:
        global players
        players = [[x.nick, 0] for x in ctx.author.voice.channel.members]
        voice = await ctx.author.voice.channel.connect()
    else:
        await ctx.send("Already in a voice channel!")


@bot.command(name = "queue", aliases = ['q'])
async def queue(ctx, url, answer):
    if voice is None:
        await ctx.send("Not in voice channel yet!")
        return

    if ctx.author.nick in playersQueued:
        await ctx.send("Already queued this round!")
        return

    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()

    # Play immediately (nothing in the queue)
    if not voice.is_playing(): 
        playFromDownloadedURL(getURL(url), answer, ctx.author.nick)
    else:
        await ctx.send("Adding to queue!")
        songQueue.append([getURL(url), answer, ctx.author.nick])
    
    playersQueued.append(ctx.author.nick)
    return

@bot.command(name = "guess", aliases = ['g'])
async def guess(ctx, answer):
    # Sanitize input, removing comma, apostrophe, dash, and parenthesis and casting to lowercase
    answer = answer.strip().replace(",", "").replace("'", "").replace("-", "").replace("(", "").replace(")", "").lower()
    if answer == songName:
        await ctx.send("Correct answer!")

@bot.command(name = "skip", aliases = ['s'])
async def skip(ctx):
    #Todo: Implement
    await ctx.send("Not implemented yet")
    return
    voice.skip()

@bot.command(name = "join", aliases = ['j'])
async def join(ctx):
    if ctx.author.nick not in [player[0] for player in players]:
        players.append([ctx.author.nick, 0])
    else:
        ctx.send("Player has already joined the session!")

@bot.command(name = "scoreboard", aliases = ['sb'])
async def score(ctx):
    # Base column size of the longest player name (TODO: add a minimum s.t. that the score can't exceed player name length)
    maxLength = len(max(players, key=lambda x : len(x[0])))

    # Formatting of score goes Header, Line, Scores within a markdown block
    header = ""
    line = ""
    scores = ""
    for player in players:
        header += player[0] + " " * (maxLength - len(player[0]) + 1) + "| "
        scores += str(player[1]) + " " * (maxLength - len(str(player[1])) + 1) + "| "
    header += "\n"
    scores += "\n"
    line = "-" * len(header) + "\n"

    await ctx.send("```\n" + header + line + scores + "```")
    return

@bot.command(name = "adjustVolume", alias = ['a', 'av'])
async def adjustVolume(_, volume):
    global songVolume
    songVolume = volume

# COMMENCE!
bot.run(TOKEN)