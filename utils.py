import discord
import asyncio

async def delete_messages(ctx, *messages):
    """Verwijder alle berichten na 30 seconden."""
    await asyncio.sleep(30)  # Wacht 30 seconden voordat je de berichten verwijdert
    for msg in messages:
        if msg:
            try:
                # Log berichtinhoud voor debuggen
                print(f"Probeer bericht te verwijderen: {msg.content}")

                # Controleer of de bot de permissie heeft om berichten te beheren
                if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                    await msg.delete()
                    print(f"Verwijderd bericht ID: {msg.id}, Inhoud: '{msg.content}'")
                else:
                    print("De bot heeft geen toestemming om berichten te verwijderen.")
            except discord.NotFound:
                print(f"Bericht {msg.id if msg else 'onbekend'} was al verwijderd.")
            except discord.Forbidden:
                print("De bot heeft geen toestemming om berichten te verwijderen.")
            except Exception as e:
                print(f"Fout bij het verwijderen van bericht {msg.id if msg else 'onbekend'}: {e}")
        else:
            print("Geen bericht om te verwijderen.")
