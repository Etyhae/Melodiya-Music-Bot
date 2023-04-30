import discord
from discord.ext import commands
from config import settings
from yandex_music import Client
import asyncio


clientYM = Client(settings['YM_token']).init()

clientYM.users_likes_tracks()[0].fetch_track().download('first.mp3')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)
QUEUE = []
loopIs = False

def song_search(songName, downloadQueue):
    search_result = clientYM.search(songName)
    trackID = search_result['best']['result']['id']
    albumID = search_result['best']['result']['albums'][0]['id']
    trackName = search_result['best']['result']['title']
    trackFull = {trackID : albumID}
    clientYM.tracks([trackFull])[0].download(f'{downloadQueue}.mp3')
    return trackName

async def playSong(ctx, FoS):
    user = ctx.author
    channel = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice == None:
        voice_channel = user.voice.channel
        # only play music if user is in a voice channel
        if voice_channel != None:
            vc = await channel.connect(self_deaf=True)
            vc.play(discord.FFmpegPCMAudio(executable=r"C:/ffmpeg/bin/ffmpeg.exe", source=rf"C:\Users\maxma\Desktop\Py\Disc\{FoS}.mp3"))
    else:
        voice.play(discord.FFmpegPCMAudio(executable=r"C:/ffmpeg/bin/ffmpeg.exe", source=rf"C:\Users\maxma\Desktop\Py\Disc\{FoS}.mp3"))

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
@bot.command()
async def pl(ctx):
    global loopIs
    loopIs = loopIs
    user = ctx.author
    channel = user.voice.channel
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice == None:
        voice_channel = user.voice.channel
        # only play music if user is in a voice channel
        if voice_channel != None:
            vc = await channel.connect(self_deaf=True)
            vc.play(discord.FFmpegPCMAudio(executable=r"C:/ffmpeg/bin/ffmpeg.exe", source=rf"C:\Users\maxma\Desktop\Py\Disc\first.mp3"))
        while vc.is_playing():
            await asyncio.sleep(1)
        if loopIs:
            await pl(ctx)
        else:
            await ctx.send("Плейлист закончился")
    else:
        voice.play(discord.FFmpegPCMAudio(executable=r"C:/ffmpeg/bin/ffmpeg.exe", source=rf"C:\Users\maxma\Desktop\Py\Disc\first.mp3"))
        while voice.is_playing():
            await asyncio.sleep(1)
        if loopIs:
            await pl(ctx)
        else:
            await ctx.send("Плейлист закончился")

@bot.command()
async def loop(ctx):
    global loopIs
    loopIs = not loopIs
    await ctx.send(f'Loop = {loopIs}')

@bot.command()
async def search(ctx, *args):
    arguments = ', '.join(args)
    search_result = clientYM.search(arguments)
    trackID = search_result['best']['result']['id']
    albumID = search_result['best']['result']['albums'][0]['id']
    trackName = search_result['best']['result']['title']
    artistName = search_result['best']['result']['artists'][0]['name']
    trackFull = {trackID : albumID}
    clientYM.tracks([trackFull])[0].download('first.mp3')
    await ctx.send(f'{trackName}' + ' - ' + f'{artistName}')


@bot.command()
async def play(ctx, *args):
    #arguments join in one string
    arguments = ', '.join(args)
    queList = ""
    #playing music
    if QUEUE.count == 0:
        #search song
        QUEUE.append(song_search(arguments, 0))
        playSong(ctx)
        await ctx.send(QUEUE[0])
    else:
        QUEUE.append(song_search(arguments, QUEUE.count))
        for x in range(QUEUE.count()):
            queList += f"{QUEUE[x]} \n" 
        await ctx.send(queList)

@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        if(voice.is_paused()):
            await ctx.send("Ошибка: Аудио на паузе")
        else:
            voice.resume()
    else:
        await ctx.send("Бот не в голосовом канале")

@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        if(voice.is_paused()):
            voice.resume()
        else:
            await ctx.send("Ошибка: Аудио воспроизводится")
    else:
        await ctx.send("Бот не в голосовом канале")

@bot.command()
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice.is_connected()):
        voice.stop()
    else:
        await ctx.send("Бот не в голосовом канале")

bot.run(settings['token'])