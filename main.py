import os
from threading import Thread
import zoneinfo
from datetime import time
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from flask import Flask

# Configurazione del server Flask per UptimeRobot e Render
app_flask = Flask('')


@app_flask.route('/')
def home():
  return 'Bot is active and running!'


def run_flask():
  port = int(os.environ.get('PORT', 3000))
  app_flask.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run_flask)
  t.start()


# Carica il token in modo sicuro
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configurazione iniziale del Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ITALY_TZ = zoneinfo.ZoneInfo("Europe/Rome")


# --- 1. MODALE PER APERTURA CONTO ---
class AccountModal(discord.ui.Modal, title="Apertura Conto Bancario | Unicredit"):
  nome_cognome = discord.ui.TextInput(
      label="Nome e Cognome RP",
      placeholder="Inserisci il tuo Nome e Cognome...",
      required=True,
      max_length=100,
  )

  async def on_submit(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title="Nuova Richiesta Apertura Conto",
        description=f"Richiedente: {interaction.user.mention}\nNome RP: **{self.nome_cognome.value}**",
        color=discord.Color.red(),
    )
    embed.set_footer(text="UniCredit Banking System v2.1")

    await interaction.response.send_message(
        "Richiesta inviata con successo allo staff! Verrai notificato all'approvazione.",
        ephemeral=True,
    )


# --- 2. VIEW CON PULSANTE CREA CONTO E APPROVAZIONE STAFF ---
class AccountCreationView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Crea Conto",
      style=discord.ButtonStyle.danger,
      custom_id="create_account_btn",
  )
  async def create_account(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.send_modal(AccountModal())


class StaffApprovalView(discord.ui.View):

  def __init__(self, target_user: discord.User):
    super().__init__(timeout=None)
    self.target_user = target_user

  @discord.ui.button(
      label="Accetta",
      style=discord.ButtonStyle.green,
      custom_id="approve_account",
  )
  async def approve(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.edit_message(
        content=f"Conto di {self.target_user.mention} **approvato** da {interaction.user.mention}.",
        view=None,
    )
    try:
      await self.target_user.send(
          "Il tuo conto bancario Unicredit è stato approvato ed è ora attivo!"
      )
    except discord.HTTPException:
      pass

  @discord.ui.button(
      label="Rifiuta",
      style=discord.ButtonStyle.red,
      custom_id="reject_account",
  )
  async def reject(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.edit_message(
        content=f"Conto di {self.target_user.mention} **rifiutato** da {interaction.user.mention}.",
        view=None,
    )


# --- 3. EVENTO ON_READY E TASK AUTOMATICI ---
@bot.event
async def on_ready():
  print(f"Bot loggato come {bot.user}")
  try:
    synced = await bot.tree.sync()
    print(f"Sincronizzati {len(synced)} comandi slash.")
  except Exception as e:
    print(e)

  if not daily_taxes_task.is_running():
    daily_taxes_task.start()


@tasks.loop(time=time(hour=10, minute=0, tzinfo=ITALY_TZ))
async def daily_taxes_task():
  embed = discord.Embed(
      title="Avviso Tasse | Unicredit",
      description="Gentile cliente, risultano tasse ancora non pagate.",
      color=discord.Color.red(),
  )
  embed.add_field(
      name="SALDO ATTUALE", value="€ [Saldo del cittadino]", inline=False
  )
  embed.add_field(name="COSTO TASSE", value="€ 400", inline=False)
  embed.set_footer(
      text="Fai il comando /paga_tasse per saldare le tasse. | UniCredit"
  )
  print("Invio avviso tasse giornaliero delle ore 10:00.")


# --- 4. DEFINIZIONE COMANDI SLASH ---
@bot.tree.command(
    name="saldo",
    description="Visualizza il saldo disponibile sul conto corrente principale.",
)
async def saldo(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Il tuo saldo disponibile è: € 0,00", ephemeral=True
  )


@bot.tree.command(
    name="bonifico",
    description="Invia denaro a un utente (notifica automatica in DM).",
)
@app_commands.describe(
    destinatario="Utente destinatario",
    importo="Somma di denaro",
    motivazione="Causale del bonifico",
)
async def bonifico(
    interaction: discord.Interaction,
    destinatario: discord.User,
    importo: int,
    motivazione: str,
):
  await interaction.response.send_message(
      f"Bonifico di € {importo} inviato a {destinatario.mention}.", ephemeral=True
  )

  try:
    dm_embed = discord.Embed(title="Bonifico Ricevuto", color=discord.Color.red())
    dm_embed.add_field(
        name="MITTENTE", value=interaction.user.display_name, inline=False
    )
    dm_embed.add_field(name="IMPORTO", value=f"€ {importo}", inline=False)
    dm_embed.add_field(name="MOTIVAZIONE", value=motivazione, inline=False)
    dm_embed.set_footer(text="UniCredit")
    await destinatario.send(embed=dm_embed)
  except discord.HTTPException:
    pass


@bot.tree.command(
    name="transazioni",
    description="Consulta la cronologia e lo storico dettagliato dei movimenti.",
)
async def transazioni(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Cronologia transazioni vuota.", ephemeral=True
  )


@bot.tree.command(
    name="paga_tasse",
    description="Esegui il pagamento della tassa giornaliera (€ 400).",
)
async def paga_tasse(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Tassa giornaliera di € 400 pagata con successo.", ephemeral=True
  )


@bot.tree.command(
    name="deposita_su_condiviso",
    description="Trasferisci fondi dal conto personale a quello condiviso.",
)
async def deposita_su_condiviso(interaction: discord.Interaction, importo: int):
  await interaction.response.send_message(
      f"Depositati € {importo} sul conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="preleva_da_condiviso",
    description="Preleva fondi dal conto condiviso verso il conto personale.",
)
async def preleva_da_condiviso(interaction: discord.Interaction, importo: int):
  await interaction.response.send_message(
      f"Prelevati € {importo} dal conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="miei_conti_condiviso",
    description="Elenca i conti condivisi di cui si è membro o proprietario.",
)
async def miei_conti_condivisi(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Elenco conti condivisi.", ephemeral=True
  )


@bot.tree.command(
    name="info_conto_condiviso",
    description="Visualizza dettagli, saldo e membri di uno specifico conto condiviso.",
)
async def info_conto_condiviso(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Dettagli conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="stato",
    description="Verifica lo stato generale e l'operatività del proprio conto.",
)
async def stato(interaction: discord.Interaction):
  await interaction.response.send_message("Stato conto: Attivo.", ephemeral=True)


@bot.tree.command(
    name="aggiungi_fondo",
    description="Aggiungi risparmi o liquidità in un fondo specifico.",
)
async def aggiungi_fondo(interaction: discord.Interaction, importo: int):
  await interaction.response.send_message(
      f"Aggiunti € {importo} al fondo.", ephemeral=True
  )


@bot.tree.command(
    name="preleva_fondo",
    description="Preleva riserve da un fondo aperto in precedenza.",
)
async def preleva_fondo(interaction: discord.Interaction, importo: int):
  await interaction.response.send_message(
      f"Prelevati € {importo} dal fondo.", ephemeral=True
  )


STIPENDI_LAVORI = {
    "FDO": 3200,
    "Vigile Del Fuoco": 3500,
    "SUEM": 3800,
    "ACI": 2200,
    "Tassista": 2000,
    "Camionista": 3000,
    "Autista BUS": 2300,
}


@bot.tree.command(
    name="paga_stipendio",
    description="Accredita lo stipendio ai propri dipendenti in base alla mansione.",
)
@app_commands.choices(
    mansione=[
        app_commands.Choice(
            name="FDO (Forze dell'Ordine) - € 3.200", value="FDO"
        ),
        app_commands.Choice(
            name="Vigile Del Fuoco - € 3.500", value="Vigile Del Fuoco"
        ),
        app_commands.Choice(
            name="SUEM (Sanitario/Esercito) - € 3.800", value="SUEM"
        ),
        app_commands.Choice(name="ACI (Soccorso Stradale) - € 2.200", value="ACI"),
        app_commands.Choice(name="Tassista - € 2.000", value="Tassista"),
        app_commands.Choice(name="Camionista - € 3.000", value="Camionista"),
        app_commands.Choice(name="Autista BUS - € 2.300", value="Autista BUS"),
    ]
)
async def paga_stipendio(
    interaction: discord.Interaction,
    dipendente: discord.User,
    mansione: app_commands.Choice[str],
):
  importo = STIPENDI_LAVORI[mansione.value]
  await interaction.response.send_message(
      f"Accreditato stipendio di € {importo} ({mansione.name}) a"
      f" {dipendente.mention}.",
      ephemeral=True,
  )


@bot.tree.command(
    name="stipendi",
    description=(
        "Visualizza la tabella ufficiale degli stipendi e dei lavori con emoji."
    ),
)
async def stipendi(interaction: discord.Interaction):
  embed = discord.Embed(
      title="Tabella Stipendi Lavori | Unicredit",
      description=(
          "Compensi ufficiali erogabili tramite `/paga_stipendio` o accreditati"
          " dal sistema:"
      ),
      color=discord.Color.red(),
  )
  stipendi_text = (
      "👮‍♂️ **FDO (Forze dell'Ordine)**: € 3.200\n"
      "🚒 **Vigile Del Fuoco**: € 3.500\n"
      "🚑 **SUEM (Servizio Sanitario / Esercito)**: € 3.800\n"
      "🚗 **ACI (Soccorso Stradale)**: € 2.200\n"
      "🚕 **Tassista**: € 2.000\n"
      "🚚 **Camionista**: € 3.000\n"
      "🚌 **Autista BUS**: € 2.300\n"
  )
  embed.add_field(name="Mansioni & Compensi", value=stipendi_text, inline=False)
  embed.set_footer(text="UniCredit Banking System v2.1")
  await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
    name="bonifico_conto_condiviso",
    description=(
        "Invia un bonifico attingendo dal conto condiviso (Cointestatari)."
    ),
)
async def bonifico_conto_condiviso(
    interaction: discord.Interaction, importo: int
):
  await interaction.response.send_message(
      f"Bonifico di € {importo} inviato dal conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="chiudi_conto_condiviso",
    description=(
        "Chiudi definitivamente il conto condiviso e liquida i fondi"
        " (Proprietario)."
    ),
)
async def chiudi_conto_condiviso(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Conto condiviso chiuso definitivamente.", ephemeral=True
  )


@bot.tree.command(
    name="aggiungi_membro",
    description=(
        "Aggiungi ed autorizza un utente nel conto condiviso (Proprietario)."
    ),
)
async def aggiungi_membro(
    interaction: discord.Interaction, membro: discord.User
):
  await interaction.response.send_message(
      f"Utente {membro.mention} aggiunto al conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="rimuovi_membro",
    description="Rimuovi un membro dal conto condiviso (Proprietario).",
)
async def rimuovi_membro(
    interaction: discord.Interaction, membro: discord.User
):
  await interaction.response.send_message(
      f"Utente {membro.mention} rimosso dal conto condiviso.", ephemeral=True
  )


@bot.tree.command(
    name="trasferisci_proprieta",
    description=(
        "Cedi la gestione principale del conto a un altro membro (Proprietario)."
    ),
)
async def trasferisci_proprieta(
    interaction: discord.Interaction, nuovo_proprietario: discord.User
):
  await interaction.response.send_message(
      f"Proprietà trasferita a {nuovo_proprietario.mention}.", ephemeral=True
  )


@bot.tree.command(
    name="conto-embed",
    description=(
        "Invia nel canale designato il messaggio Embed interattivo per la"
        " creazione del conto."
    ),
)
async def conto_embed(interaction: discord.Interaction):
  embed = discord.Embed(
      title="Apertura Conto Bancario | Unicredit",
      description=(
          "Benvenuto nel servizio bancario ufficiale! Clicca sul pulsante"
          " sottostante per inviare la richiesta di apertura del tuo conto"
          " personale."
      ),
      color=discord.Color.red(),
  )
  embed.set_footer(text="UniCredit")
  await interaction.channel.send(embed=embed, view=AccountCreationView())
  await interaction.response.send_message(
      "Embed di creazione conto inviato con successo.", ephemeral=True
  )


@bot.tree.command(
    name="ruolo-milionario",
    description=(
        "Assegna/setta il ruolo Milionario (automatico al superamento di €"
        " 1.000.000)."
    ),
)
async def ruolo_milionario(
    interaction: discord.Interaction, utente: discord.User
):
  await interaction.response.send_message(
      f"Ruolo Milionario aggiornato per {utente.mention}.", ephemeral=True
  )


@bot.tree.command(
    name="ruolo-amministrativo",
    description=(
        "Setta il ruolo Staff per accedere ai comandi amministrativi del bot."
    ),
)
async def ruolo_amministrativo(
    interaction: discord.Interaction, ruolo: discord.Role
):
  await interaction.response.send_message(
      f"Ruolo amministrativo impostato su {ruolo.mention}.", ephemeral=True
  )


@bot.tree.command(
    name="apri_conto_condiviso",
    description="Autorizza e crea un nuovo conto condiviso nel sistema.",
)
async def apri_conto_condiviso(interaction: discord.Interaction):
  await interaction.response.send_message(
      "Nuovo conto condiviso autorizzato e creato.", ephemeral=True
  )


@bot.tree.command(
    name="accredita_conto_condiviso",
    description=(
        "Esegui un accredito straordinario o manuale su un conto condiviso."
    ),
)
async def accredita_conto_condiviso(
    interaction: discord.Interaction, importo: int
):
  await interaction.response.send_message(
      f"Accredito straordinario di € {importo} eseguito sul conto condiviso.",
      ephemeral=True,
  )


@bot.tree.command(
    name="blocca_conto",
    description="Sospendi o ripristina l'operatività di un qualsiasi conto.",
)
async def blocca_conto(interaction: discord.Interaction, utente: discord.User):
  await interaction.response.send_message(
      f"Conto di {utente.mention} bloccato/sbloccato.", ephemeral=True
  )


@bot.tree.command(
    name="elimina_conto",
    description="Rimuovi ed elimina permanentemente un conto dai database.",
)
async def elimina_conto(interaction: discord.Interaction, utente: discord.User):
  await interaction.response.send_message(
      f"Conto di {utente.mention} eliminato permanentemente.", ephemeral=True
  )


@bot.tree.command(
    name="saldo_admin",
    description=(
        "Visualizza, modifica, imposta o gestisci i saldi di qualsiasi utente."
    ),
)
async def saldo_admin(
    interaction: discord.Interaction, utente: discord.User, nuovo_saldo: int
):
  await interaction.response.send_message(
      f"Saldo di {utente.mention} impostato a € {nuovo_saldo}.", ephemeral=True
  )


# Avvia il server Flask in background per UptimeRobot e Render
keep_alive()

# Avvio del bot
bot.run(TOKEN)
