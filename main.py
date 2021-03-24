import os
from asyncio import sleep
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from youtube_dl import YoutubeDL

from Yapi import Yapi

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

PREFERRED_QUALITY = '192'
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'simulate': 'True',
    'noplaylist': 'True',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '64',
    }]}

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -loglevel panic'}

bot = commands.Bot(command_prefix='!!')

yapi = Yapi()
vc = None  # voice client


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.PrivateMessageOnly):
        await ctx.send(
            f'{ctx.message.author.mention}, \n'
            f'Available only in direct messages :tired_face:')
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(
            f"{ctx.message.author.mention}, \n"
            f"That command wasn't found! Sorry :tired_face:")


@bot.command(aliases=['lgn', 'l'])
@commands.dm_only()
async def login(ctx, _login_or_token: str = '', _pwd: str = ''):
    global yapi

    if _pwd == '' and _login_or_token == '':
        await ctx.send(f'{ctx.message.author.mention}, DEBUG login')

    if await yapi.init(_login_or_token, _pwd):
        await ctx.send(f'{ctx.message.author.mention}, Login success :white_check_mark:')
        print("Success")
    else:
        await ctx.send(f'{ctx.message.author.mention}, Login fail :no_entry:')
        print("Failure")


@bot.command()
async def fav_count(ctx):
    global yapi
    playlist = yapi.get_user_likes_tracks()
    await ctx.send(len(playlist))


@bot.command(aliases=['playlist', 'list'])
async def pl(ctx, start_from: int = 0, end_on: int = -1):
    global yapi

    if yapi.client is not None:
        await ctx.send(
            f'{ctx.message.author.mention}, :slot_machine: Get info about playlist.\nif there are more than 20 tracks, '
            f'the search for information will take longer')

        playlist = yapi.get_user_likes_tracks()
        short_tracks = playlist.tracks

        if end_on == -1:
            end_on = len(short_tracks)

        full_name_of_song = ''
        _end_on = end_on
        if _end_on > start_from + 25:
            await ctx.send(
                f'{ctx.message.author.mention}, :slot_machine: Get info about 25 tracks from {start_from} position')
            _end_on = start_from + 25

        for i in range(start_from, _end_on + 1):
            track = short_tracks[i].track if short_tracks[i].track else short_tracks[i].fetchTrack()
            artist_string = ''
            for a in track.artists:
                artist_string += ' ' + a.name

            full_name_of_song += str(i) + '. ' + artist_string + ' ~ ' + track.title + "\n"

        await ctx.send(f'{ctx.message.author.mention}, \n{full_name_of_song}')

    else:
        await ctx.send(
            f'{ctx.message.author.mention}, Unauthorized :passport_control: \n'
            f'Use on of two commands in direct messages:\n'
            f' - :loudspeaker: "**!!login username password**"\n'
            f' - :loudspeaker: "**!!login token**"')


@bot.command(aliases=['play fav', 'play favorite'])
async def pf(ctx, start_from: int = 0, end_on: int = -1, stream: bool = "True"):
    """
    Play favourite playlist from music.yandex.ru
    To use it need `login` function

    :param ctx: Discord context
    :param start_from: Start from song position
    :param end_on: End to song position
    :param stream: True - use stream function for play music. False - use local file
    """
    global vc
    global yapi

    if yapi.client is not None:
        voice_status = ctx.author.voice
        if voice_status:  # this check does nothing. This is a discord.VoiceState object
            channel = voice_status.channel
            # channel is None if you are not connected to a voice channel
            # channel is a Channel object if you are connected to a voice channel
            if ctx.voice_client is None:
                # I may be wrong but if I read the docs right this returns the voice client of the guild,
                # something semi-related to the author.
                vc = await channel.connect()
                # You are not connected to a voice channel. So channel is None.
                # Now you are trying to connect to a None channel.
                print("Connect")

        playlist = yapi.get_user_likes_tracks()
        short_tracks = playlist.tracks

        if end_on == -1:
            end_on = len(short_tracks)

        if vc.is_playing():
            await ctx.send(f'{ctx.message.author.mention}, Music already playing.')
            vc.pause()

        print(f'for {start_from} in {end_on}')
        await ctx.send(f'{ctx.message.author.mention}, :slot_machine: Get information about tracks list')

        full_name_of_song = ''
        _end_on = end_on
        if _end_on > start_from + 10:
            _end_on = start_from + 10

        for i in range(start_from, _end_on):
            track = short_tracks[i].track if short_tracks[i].track else short_tracks[i].fetchTrack()
            artist_string = ''
            for a in track.artists:
                artist_string += ' ' + a.name

            full_name_of_song += str(i) + '. ' + artist_string + ' ~ ' + track.title + "\n"

        await ctx.send(f'{ctx.message.author.mention}, \n{full_name_of_song}')

        # for short_track in short_tracks:
        for i in range(start_from, end_on):
            if vc.is_connected():
                track = short_tracks[i].track if short_tracks[i].track else short_tracks[i].fetchTrack()

                print('|'.join(a.name for a in track.artists), end='')
                print(f" [{'|'.join(a.title for a in track.albums)}]", '~', track.title)

                artist_dir = Path(f'{track.artists[0].name}_{track.artists[0].id}')
                album_dir = Path(f'{track.albums[0].title}_{track.albums[0].id}')
                file_path = 'music/' / artist_dir / album_dir / f'{track.title}_{track.id}.mp3'

                file_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    print('Downloading...')
                    track.download(file_path, 'mp3', int(PREFERRED_QUALITY))

                    direct_link = track.download_info[0].direct_link

                    await ctx.send(
                        f'{ctx.message.author.mention}, :play_pause:'
                        f' Start playing {track.artists[0].name} - {track.title}')
                    if stream:
                        await play_stream(vc, direct_link)
                    else:
                        await play_download(vc, file_path)

                except Exception as e:
                    print('Error:', e)

                while vc.is_playing():
                    await sleep(1)
                if vc.is_paused():
                    print("Paused")
                    break

        if not vc.is_playing() and not vc.is_paused():
            await vc.disconnect()

    else:
        await ctx.send(
            f'{ctx.message.author.mention}, Unauthorized :passport_control: \n'
            f'Use on of two commands in direct messages:\n'
            f' - :loudspeaker: "**!!login username password**"\n'
            f' - :loudspeaker: "**!!login token**"')


async def play_download(_vc, _file_path):
    """
    Play mp3 file local from OS

    :param _vc: Voice controller
    :param _file_path: Path to mp3 file
    """

    _vc.play(discord.FFmpegPCMAudio(source=_file_path))

    while _vc.is_playing():
        # if music play wait 1 sec
        await sleep(1)
    if not _vc.is_paused():
        print("Next song")


async def play_stream(_vc, _direct_link):
    """
    Play mp3 file from URL

    :param _vc: Voice controller
    :param _direct_link: Direct url to mp3 file
    """

    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(_direct_link, download=False)

        url = info['formats'][0]['url']

        _vc.play(discord.FFmpegPCMAudio(source=url, **FFMPEG_OPTIONS))

        while _vc.is_playing():
            await sleep(1)
        if not _vc.is_paused():
            print("Next song")


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.command()
async def stop(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.pause()


@commands.command()
async def play(ctx, *, query):
    """Plays a file from the local filesystem"""

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
    ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(query))


if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)
