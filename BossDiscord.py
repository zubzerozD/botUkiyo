import discord
import json
import asyncio
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # Necesario para permitir que el bot lea los mensajes

bot = commands.Bot(command_prefix="!", intents=intents)

boss_names = ["Surbora", "Utumno", "Nazrudin"]
timers_per_boss = {boss: [3600 for _ in range(8)] for boss in boss_names}  # 1 hora (3600 segundos) por canal


@bot.event
async def on_ready():
    print(f'Bot {bot.user} está listo.')
    load_state()


@bot.command(name="boss")
async def boss(ctx, boss_name: str, channel: int = 1, time: int = 3600):
    """Comando para registrar la muerte de un boss en un canal. El temporizador es opcional (default: 3600s)."""
    if boss_name not in boss_names:
        await ctx.send(f"Boss '{boss_name}' no reconocido.")
        return

    if channel < 1 or channel > 8:
        await ctx.send("El canal debe estar entre 1 y 8.")
        return

    channel -= 1  # Para que sea más comprensible para el usuario (canales 1-8 en lugar de 0-7)
    timers_per_boss[boss_name][channel] = time

    await ctx.send(f"{boss_name} en el canal {channel + 1} fue derrotado. Temporizador iniciado para {time // 60} minutos.")
    
    # Iniciar el temporizador
    asyncio.create_task(start_timer(ctx, boss_name, channel, time))
    save_state()



async def start_timer(ctx, boss_name, channel, time):
    while time > 0:
        await asyncio.sleep(1)
        time -= 1
        timers_per_boss[boss_name][channel] = time
        
        # Aviso cuando queden 5 minutos
        if time == 300:
            await ctx.send(f"Faltan 5 minutos para que {boss_name} reaparezca en el canal {channel + 1}.")

    # Aviso cuando el boss reaparezca
    await ctx.send(f"{boss_name} ha reaparecido en el canal {channel + 1}!")
    save_state()


@bot.command(name="estado")
async def estado(ctx, boss_name: str):
    """Verifica el estado de los temporizadores de un boss y actualiza cada segundo."""
    if boss_name not in boss_names:
        await ctx.send(f"Boss '{boss_name}' no reconocido.")
        return

    message = await ctx.send(f"Mostrando temporizadores para {boss_name}...")

    while any(t > 0 for t in timers_per_boss[boss_name]):
        status_message = f"**Estado de los temporizadores para {boss_name}:**\n"
        for channel, time in enumerate(timers_per_boss[boss_name], 1):
            minutes, seconds = divmod(time, 60)
            status_message += f"Canal {channel}: {minutes:02d}:{seconds:02d}\n"
        
        await message.edit(content=status_message)
        await asyncio.sleep(1)  # Espera 1 segundo antes de actualizar nuevamente

    # Una vez que todos los temporizadores lleguen a 0
    await message.edit(content=f"Todos los canales de {boss_name} están listos. ¡Boss renacido en todos los canales!")
    save_state()


@bot.command(name="clear_history")
async def clear_history(ctx):
    """Limpia el estado de los temporizadores (resetea todo a 3600 segundos)."""
    global timers_per_boss
    timers_per_boss = {boss: [3600 for _ in range(8)] for boss in boss_names}
    save_state()
    await ctx.send("Se ha reiniciado el estado de los temporizadores.")


def save_state():
    """Guarda el estado actual de los temporizadores en un archivo JSON."""
    state = {}
    for boss in boss_names:
        state[boss] = timers_per_boss[boss]
    
    with open("timers_state.json", "w") as file:
        json.dump(state, file)


def load_state():
    """Carga el estado de los temporizadores desde un archivo JSON."""
    global timers_per_boss
    try:
        with open("timers_state.json", "r") as file:
            state = json.load(file)
            # Verificar que se carguen solo listas de tiempos
            for boss in state:
                if isinstance(state[boss], list):
                    timers_per_boss[boss] = [int(timer) for timer in state[boss]]
    except FileNotFoundError:
        print("Archivo de estado no encontrado, se usará el estado predeterminado.")
    except ValueError as e:
        print(f"Error de formato en el archivo JSON: {e}")

# Reemplaza 'your-token-here' con tu token real del bot
bot.run('NzkwMzA5OTA0NjE1MDc5OTM3.GQKh7R.UVNs1oaMrBbmwxKeI3xOqTphg_7jhwTPpYFMmE')
