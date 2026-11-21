"""core.py — parte generale: lingua (IT/EN), grafica (CSS), roster atleti, costanti e funzioni condivise."""
import base64
import glob
import hmac
import html as html_lib
import io
import json
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from urllib.parse import quote, urljoin
import altair as alt
import pandas as pd
import requests
import streamlit as _st_real

# ------------------------------------------------------------------------------
# 0. Lingua (italiano / inglese)
#    Il testo del sito è scritto in italiano; in inglese viene tradotto al volo
#    con i dizionari qui sotto. Se una frase non è nel dizionario resta in italiano.
# ------------------------------------------------------------------------------
EN_STATIC = {'Palleggiatore': 'Setter',
 'Schiacciatore': 'Outside Hitter',
 'Opposto': 'Opposite',
 'Centrale': 'Middle Blocker',
 'Libero': 'Libero',
 'Atleta': 'Athlete',
 'Esercizio': 'Exercise',
 "gcp_service_account_json non è un JSON valido: incolla l'intero file scaricato da Google, dalla { iniziale alla } finale.": 'gcp_service_account_json '
                                                                                                                              'is '
                                                                                                                              'not '
                                                                                                                              'valid '
                                                                                                                              'JSON: '
                                                                                                                              'paste '
                                                                                                                              'the '
                                                                                                                              'whole '
                                                                                                                              'file '
                                                                                                                              'downloaded '
                                                                                                                              'from '
                                                                                                                              'Google, '
                                                                                                                              'from '
                                                                                                                              'the '
                                                                                                                              'opening '
                                                                                                                              '{ '
                                                                                                                              'to '
                                                                                                                              'the '
                                                                                                                              'closing '
                                                                                                                              '}.',
 'La private_key nei secrets non è completa: deve iniziare con -----BEGIN PRIVATE KEY----- (è il valore reale del file JSON, non i puntini di esempio).': 'The '
                                                                                                                                                          'private_key '
                                                                                                                                                          'in '
                                                                                                                                                          'the '
                                                                                                                                                          'secrets '
                                                                                                                                                          'is '
                                                                                                                                                          'incomplete: '
                                                                                                                                                          'it '
                                                                                                                                                          'must '
                                                                                                                                                          'start '
                                                                                                                                                          'with '
                                                                                                                                                          '-----BEGIN '
                                                                                                                                                          'PRIVATE '
                                                                                                                                                          'KEY----- '
                                                                                                                                                          '(it '
                                                                                                                                                          'is '
                                                                                                                                                          'the '
                                                                                                                                                          'real '
                                                                                                                                                          'value '
                                                                                                                                                          'from '
                                                                                                                                                          'the '
                                                                                                                                                          'JSON '
                                                                                                                                                          'file, '
                                                                                                                                                          'not '
                                                                                                                                                          'the '
                                                                                                                                                          'sample '
                                                                                                                                                          'dots).',
 'Manca apps_script_key nei secrets di Streamlit.': 'apps_script_key is missing from the Streamlit '
                                                    'secrets.',
 'Mancano apps_script_url o apps_script_key nei secrets.': 'apps_script_url or apps_script_key is '
                                                           'missing from the secrets.',
 'verrà creata al primo salvataggio': 'will be created on the first save',
 'Mancano le credenziali Google nei secrets di Streamlit (gcp_service_account_json).': 'Google '
                                                                                       'credentials '
                                                                                       'are '
                                                                                       'missing '
                                                                                       'from the '
                                                                                       'Streamlit '
                                                                                       'secrets '
                                                                                       '(gcp_service_account_json).',
 'A · Forza': 'A · Strength',
 'B · Forza esplosiva': 'B · Explosive strength',
 'C · Forza esplosiva': 'C · Explosive strength',
 'manca la libreria openpyxl (aggiungila al requirements.txt)': 'the openpyxl library is missing '
                                                                '(add it to requirements.txt)',
 'Leggo le schede settimanali…': 'Reading the weekly plans…',
 'Periodo': 'Period',
 'Scheda': 'Sheet',
 'Esito': 'Result',
 'Serie lette': 'Sets read',
 'nessun carico trovato': 'no load found',
 '🚀\n\nDataJump\n\nMonitoraggio Salti, Elevazione & Fasce': '🚀\n'
                                                            '\n'
                                                            'DataJump\n'
                                                            '\n'
                                                            'Jump monitoring, elevation & bands',
 '🏋️\u200d♂️\n\nDataLoad\n\nMonitoraggio Carichi, Massimali & Forza': '🏋️\u200d♂️\n'
                                                                      '\n'
                                                                      'DataLoad\n'
                                                                      '\n'
                                                                      'Load, max & strength '
                                                                      'monitoring',
 '### 🚀 **DataJump** — Monitoraggio Salti & Elevazione': '### 🚀 **DataJump** — Jump & Elevation '
                                                         'Monitoring',
 '🏠 Torna alla Home': '🏠 Back to Home',
 '🔓 Visualizzazione: Roster Completo': '🔓 View: Full roster',
 '⚠️ Nessun file CSV relativo ai salti trovato.': '⚠️ No CSV file with jump data found.',
 '🔍 Filtri Selezione & Confronto': '🔍 Selection & Comparison Filters',
 'Filtra per Ruolo': 'Filter by role',
 'Seleziona Giocatori da Analizzare / Confrontare': 'Select players to analyze / compare',
 'Settimane di Lavoro': 'Training weeks',
 'Date Sedute': 'Session dates',
 'Totale Salti': 'Total jumps',
 '📊 Andamento Giornaliero': '📊 Daily trend',
 '🗓️ Andamento Settimanale': '🗓️ Weekly trend',
 '⚔️ Confronto Giocatori': '⚔️ Player comparison',
 '🎯 Distribuzione Fasce': '🎯 Band distribution',
 '🆚 Confronto Settimane': '🆚 Week comparison',
 '##### 🔵 Volume Salti per Data e Giocatore — ultime 7 sedute': '##### 🔵 Jump volume by date and '
                                                                'player — last 7 sessions',
 'Data Seduta': 'Session date',
 'Nr. Salti': 'No. of jumps',
 'Giocatore': 'Player',
 '🟠 Colonna / pallino arancione = giorno di partita': '🟠 Orange column / dot = match day',
 '##### 🚀 Salto Max (cm) — ultime 7 sedute': '##### 🚀 Max jump (cm) — last 7 sessions',
 'Salto Max (cm)': 'Max jump (cm)',
 "I grafici seguenti mostrano l'altezza dei singoli salti in ordine cronologico per ciascuna seduta di allenamento dell'atleta, in base all'orario in cui sono stati eseguiti.": 'The '
                                                                                                                                                                                 'charts '
                                                                                                                                                                                 'below '
                                                                                                                                                                                 'show '
                                                                                                                                                                                 'the '
                                                                                                                                                                                 'height '
                                                                                                                                                                                 'of '
                                                                                                                                                                                 'each '
                                                                                                                                                                                 'jump '
                                                                                                                                                                                 'in '
                                                                                                                                                                                 'chronological '
                                                                                                                                                                                 'order '
                                                                                                                                                                                 'for '
                                                                                                                                                                                 'every '
                                                                                                                                                                                 'training '
                                                                                                                                                                                 'session '
                                                                                                                                                                                 'of '
                                                                                                                                                                                 'the '
                                                                                                                                                                                 'athlete, '
                                                                                                                                                                                 'based '
                                                                                                                                                                                 'on '
                                                                                                                                                                                 'the '
                                                                                                                                                                                 'time '
                                                                                                                                                                                 'they '
                                                                                                                                                                                 'were '
                                                                                                                                                                                 'performed.',
 "Nei file CSV non trovo l'orario dei salti (né dentro la colonna DATE né in una colonna TIME / ORA / ORARIO / HOUR): sull'asse orizzontale mostro quindi il numero progressivo del salto.": 'I '
                                                                                                                                                                                             "can't "
                                                                                                                                                                                             'find '
                                                                                                                                                                                             'the '
                                                                                                                                                                                             'jump '
                                                                                                                                                                                             'time '
                                                                                                                                                                                             'in '
                                                                                                                                                                                             'the '
                                                                                                                                                                                             'CSV '
                                                                                                                                                                                             'files '
                                                                                                                                                                                             '(neither '
                                                                                                                                                                                             'inside '
                                                                                                                                                                                             'the '
                                                                                                                                                                                             'DATE '
                                                                                                                                                                                             'column '
                                                                                                                                                                                             'nor '
                                                                                                                                                                                             'in '
                                                                                                                                                                                             'a '
                                                                                                                                                                                             'TIME '
                                                                                                                                                                                             '/ '
                                                                                                                                                                                             'ORA '
                                                                                                                                                                                             '/ '
                                                                                                                                                                                             'ORARIO '
                                                                                                                                                                                             '/ '
                                                                                                                                                                                             'HOUR '
                                                                                                                                                                                             'column): '
                                                                                                                                                                                             'the '
                                                                                                                                                                                             'horizontal '
                                                                                                                                                                                             'axis '
                                                                                                                                                                                             'therefore '
                                                                                                                                                                                             'shows '
                                                                                                                                                                                             'the '
                                                                                                                                                                                             'jump '
                                                                                                                                                                                             'number.',
 'Nessuna sessione trovata con i filtri attuali.': 'No session found with the current filters.',
 'Orario del salto': 'Jump time',
 'Orario': 'Time',
 'N° salto': 'Jump no.',
 'Progressione Salti nella Seduta': 'Jump progression in the session',
 'Altezza Salto (cm)': 'Jump height (cm)',
 '##### 🔵 Volume Salti Settimanali': '##### 🔵 Weekly jump volume',
 'Settimana': 'Week',
 '**Totale Salti per Giocatore**': '**Total jumps per player**',
 '**Salto Max (cm) per Giocatore**': '**Max jump (cm) per player**',
 'Fascia': 'Band',
 '##### 🆚 Confronto tra due settimane di lavoro': '##### 🆚 Comparison between two training weeks',
 'Usa i filtri Ruolo e Giocatori della barra laterale; ignora i filtri Settimane e Date Sedute, così puoi scegliere qui le due settimane.': 'Uses '
                                                                                                                                            'the '
                                                                                                                                            'Role '
                                                                                                                                            'and '
                                                                                                                                            'Players '
                                                                                                                                            'filters '
                                                                                                                                            'from '
                                                                                                                                            'the '
                                                                                                                                            'sidebar; '
                                                                                                                                            'it '
                                                                                                                                            'ignores '
                                                                                                                                            'the '
                                                                                                                                            'Weeks '
                                                                                                                                            'and '
                                                                                                                                            'Session '
                                                                                                                                            'dates '
                                                                                                                                            'filters, '
                                                                                                                                            'so '
                                                                                                                                            'you '
                                                                                                                                            'can '
                                                                                                                                            'pick '
                                                                                                                                            'the '
                                                                                                                                            'two '
                                                                                                                                            'weeks '
                                                                                                                                            'here.',
 'Servono dati di almeno due settimane per fare il confronto.': 'Data from at least two weeks is '
                                                                'needed for the comparison.',
 'Settimana A (riferimento)': 'Week A (reference)',
 'Settimana B (da confrontare)': 'Week B (to compare)',
 'Scegli due settimane diverse per il confronto.': 'Choose two different weeks to compare.',
 'Giorno': 'Day',
 'Salti': 'Jumps',
 'Max (cm)': 'Max (cm)',
 'Media (cm)': 'Avg (cm)',
 '**Volume Salti per Giorno**': '**Jump volume per day**',
 '**Salto Max (cm) per Giorno**': '**Max jump (cm) per day**',
 '🟠 Pallino arancione = giorno di partita': '🟠 Orange dot = match day',
 '**Distribuzione Fasce (% sui salti della settimana)**': "**Band distribution (% of the week's "
                                                          'jumps)**',
 '% dei salti': '% of jumps',
 'Nr. salti': 'No. of jumps',
 '**Dettaglio per Giorno**': '**Detail per day**',
 'Salto max (cm)': 'Max jump (cm)',
 'Partita': 'Match',
 '**Confronto per Giocatore**': '**Comparison per player**',
 'Δ Salti': 'Δ Jumps',
 'Δ Media (cm)': 'Δ Avg (cm)',
 '### 🏋️\u200d♂️ **DataLoad** — Carichi, Massimali & Valutazione Forza': '### 🏋️\u200d♂️ '
                                                                         '**DataLoad** — Loads, '
                                                                         'Maxes & Strength '
                                                                         'Assessment',
 '✍️ Modalità modifica attiva': '✍️ Edit mode on',
 "Modalità modifica non attiva: nei secrets dell'app non trovo `admin_token` (secrets non salvati, app non riavviata, oppure errore di scrittura nel file dei secrets).": 'Edit '
                                                                                                                                                                          'mode '
                                                                                                                                                                          'off: '
                                                                                                                                                                          'I '
                                                                                                                                                                          "can't "
                                                                                                                                                                          'find '
                                                                                                                                                                          '`admin_token` '
                                                                                                                                                                          'in '
                                                                                                                                                                          'the '
                                                                                                                                                                          "app's "
                                                                                                                                                                          'secrets '
                                                                                                                                                                          '(secrets '
                                                                                                                                                                          'not '
                                                                                                                                                                          'saved, '
                                                                                                                                                                          'app '
                                                                                                                                                                          'not '
                                                                                                                                                                          'restarted, '
                                                                                                                                                                          'or '
                                                                                                                                                                          'a '
                                                                                                                                                                          'typo '
                                                                                                                                                                          'in '
                                                                                                                                                                          'the '
                                                                                                                                                                          'secrets '
                                                                                                                                                                          'file).',
 'Modalità modifica non attiva: la chiave nel link non coincide con `admin_token` dei secrets.': 'Edit '
                                                                                                 'mode '
                                                                                                 'off: '
                                                                                                 'the '
                                                                                                 'key '
                                                                                                 'in '
                                                                                                 'the '
                                                                                                 'link '
                                                                                                 "doesn't "
                                                                                                 'match '
                                                                                                 '`admin_token` '
                                                                                                 'in '
                                                                                                 'the '
                                                                                                 'secrets.',
 '📋 Schede Settimanali': '📋 Weekly plans',
 '📈 Carichi & Massimali (tutti gli esercizi)': '📈 Loads & Maxes (all exercises)',
 '🏋️ Valutazione Forza & 1RM (Google Sheet)': '🏋️ Strength assessment & 1RM (Google Sheet)',
 '📊 Tonnellaggio & Volume Pesi': '📊 Tonnage & weight volume',
 '✍️ Inserisci Carichi': '✍️ Enter loads',
 '##### 📋 Schede Settimanali (lette dai tuoi Google Fogli)': '##### 📋 Weekly plans (read from your '
                                                             'Google Sheets)',
 'ℹ️ Nessuna cartella o file collegato. Nel Google Sheet principale crea una scheda chiamata **Settimane** e scrivi nella colonna A il link della cartella Drive che contiene i tuoi file (anche con sottocartelle per settimana), oppure, uno per riga, i link dei file. La cartella e i file devono essere condivisi come «Chiunque abbia il link → Visualizzatore».': 'ℹ️ '
                                                                                                                                                                                                                                                                                                                                                                         'No '
                                                                                                                                                                                                                                                                                                                                                                         'folder '
                                                                                                                                                                                                                                                                                                                                                                         'or '
                                                                                                                                                                                                                                                                                                                                                                         'file '
                                                                                                                                                                                                                                                                                                                                                                         'linked. '
                                                                                                                                                                                                                                                                                                                                                                         'In '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'main '
                                                                                                                                                                                                                                                                                                                                                                         'Google '
                                                                                                                                                                                                                                                                                                                                                                         'Sheet '
                                                                                                                                                                                                                                                                                                                                                                         'create '
                                                                                                                                                                                                                                                                                                                                                                         'a '
                                                                                                                                                                                                                                                                                                                                                                         'tab '
                                                                                                                                                                                                                                                                                                                                                                         'named '
                                                                                                                                                                                                                                                                                                                                                                         '**Settimane** '
                                                                                                                                                                                                                                                                                                                                                                         'and '
                                                                                                                                                                                                                                                                                                                                                                         'write '
                                                                                                                                                                                                                                                                                                                                                                         'in '
                                                                                                                                                                                                                                                                                                                                                                         'column '
                                                                                                                                                                                                                                                                                                                                                                         'A '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'link '
                                                                                                                                                                                                                                                                                                                                                                         'of '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'Drive '
                                                                                                                                                                                                                                                                                                                                                                         'folder '
                                                                                                                                                                                                                                                                                                                                                                         'containing '
                                                                                                                                                                                                                                                                                                                                                                         'your '
                                                                                                                                                                                                                                                                                                                                                                         'files '
                                                                                                                                                                                                                                                                                                                                                                         '(subfolders '
                                                                                                                                                                                                                                                                                                                                                                         'per '
                                                                                                                                                                                                                                                                                                                                                                         'week '
                                                                                                                                                                                                                                                                                                                                                                         'are '
                                                                                                                                                                                                                                                                                                                                                                         'fine), '
                                                                                                                                                                                                                                                                                                                                                                         'or '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'links '
                                                                                                                                                                                                                                                                                                                                                                         'of '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'files, '
                                                                                                                                                                                                                                                                                                                                                                         'one '
                                                                                                                                                                                                                                                                                                                                                                         'per '
                                                                                                                                                                                                                                                                                                                                                                         'row. '
                                                                                                                                                                                                                                                                                                                                                                         'The '
                                                                                                                                                                                                                                                                                                                                                                         'folder '
                                                                                                                                                                                                                                                                                                                                                                         'and '
                                                                                                                                                                                                                                                                                                                                                                         'files '
                                                                                                                                                                                                                                                                                                                                                                         'must '
                                                                                                                                                                                                                                                                                                                                                                         'be '
                                                                                                                                                                                                                                                                                                                                                                         'shared '
                                                                                                                                                                                                                                                                                                                                                                         'as '
                                                                                                                                                                                                                                                                                                                                                                         '«Anyone '
                                                                                                                                                                                                                                                                                                                                                                         'with '
                                                                                                                                                                                                                                                                                                                                                                         'the '
                                                                                                                                                                                                                                                                                                                                                                         'link '
                                                                                                                                                                                                                                                                                                                                                                         '→ '
                                                                                                                                                                                                                                                                                                                                                                         'Viewer».',
 '🔎 File e schede lette': '🔎 Files and sheets read',
 '🔄 Ricarica le schede ora': '🔄 Reload plans now',
 "Non riesco a leggere nessuna serie con carico dalle schede. Nell'elenco qui sopra trovi il motivo.": 'I '
                                                                                                       "can't "
                                                                                                       'read '
                                                                                                       'any '
                                                                                                       'set '
                                                                                                       'with '
                                                                                                       'a '
                                                                                                       'load '
                                                                                                       'from '
                                                                                                       'the '
                                                                                                       'plans. '
                                                                                                       'The '
                                                                                                       'list '
                                                                                                       'above '
                                                                                                       'shows '
                                                                                                       'the '
                                                                                                       'reason.',
 'Seduta': 'Session',
 'Il 1RM stimato (formula di Epley) è calcolato solo per Back Squat, Front Squat e Stacco quadrabar. Per tutti gli altri esercizi vedi il carico massimo e le ripetizioni fatte con quel carico. Per i manubri il peso è quello di un solo manubrio.': 'The '
                                                                                                                                                                                                                                                       'estimated '
                                                                                                                                                                                                                                                       '1RM '
                                                                                                                                                                                                                                                       '(Epley '
                                                                                                                                                                                                                                                       'formula) '
                                                                                                                                                                                                                                                       'is '
                                                                                                                                                                                                                                                       'calculated '
                                                                                                                                                                                                                                                       'only '
                                                                                                                                                                                                                                                       'for '
                                                                                                                                                                                                                                                       'Back '
                                                                                                                                                                                                                                                       'Squat, '
                                                                                                                                                                                                                                                       'Front '
                                                                                                                                                                                                                                                       'Squat '
                                                                                                                                                                                                                                                       'and '
                                                                                                                                                                                                                                                       'Trap '
                                                                                                                                                                                                                                                       'Bar '
                                                                                                                                                                                                                                                       'Deadlift. '
                                                                                                                                                                                                                                                       'For '
                                                                                                                                                                                                                                                       'all '
                                                                                                                                                                                                                                                       'other '
                                                                                                                                                                                                                                                       'exercises '
                                                                                                                                                                                                                                                       'you '
                                                                                                                                                                                                                                                       'see '
                                                                                                                                                                                                                                                       'the '
                                                                                                                                                                                                                                                       'maximum '
                                                                                                                                                                                                                                                       'load '
                                                                                                                                                                                                                                                       'and '
                                                                                                                                                                                                                                                       'the '
                                                                                                                                                                                                                                                       'reps '
                                                                                                                                                                                                                                                       'done '
                                                                                                                                                                                                                                                       'with '
                                                                                                                                                                                                                                                       'that '
                                                                                                                                                                                                                                                       'load. '
                                                                                                                                                                                                                                                       'For '
                                                                                                                                                                                                                                                       'dumbbells, '
                                                                                                                                                                                                                                                       'the '
                                                                                                                                                                                                                                                       'weight '
                                                                                                                                                                                                                                                       'is '
                                                                                                                                                                                                                                                       'that '
                                                                                                                                                                                                                                                       'of '
                                                                                                                                                                                                                                                       'a '
                                                                                                                                                                                                                                                       'single '
                                                                                                                                                                                                                                                       'dumbbell.',
 'Nessun carico per questa settimana e questa seduta.': 'No load for this week and session.',
 'Carico massimo': 'Max load',
 '1RM stimato (Epley)': 'Estimated 1RM (Epley)',
 'Tutte le serie (rip × kg)': 'All sets (reps × kg)',
 'Settimana del massimo': 'Week of the max',
 'Ultima settimana': 'Latest week',
 'Carico massimo ultima settimana': 'Max load, latest week',
 '1RM stimato max (Epley)': 'Max estimated 1RM (Epley)',
 'Settimana del 1RM': 'Week of the 1RM',
 'Carico massimo (kg)': 'Max load (kg)',
 'Serie': 'Set',
 '1RM stimato (kg)': 'Estimated 1RM (kg)',
 'Serie del carico massimo': 'Set with the max load',
 '##### ✍️ Inserisci una serie': '##### ✍️ Enter a set',
 'Questa scheda compare solo a te: chi usa il link normale vede i dati ma non può modificarli.': 'This '
                                                                                                 'tab '
                                                                                                 'is '
                                                                                                 'only '
                                                                                                 'visible '
                                                                                                 'to '
                                                                                                 'you: '
                                                                                                 'people '
                                                                                                 'using '
                                                                                                 'the '
                                                                                                 'normal '
                                                                                                 'link '
                                                                                                 'can '
                                                                                                 'see '
                                                                                                 'the '
                                                                                                 'data '
                                                                                                 'but '
                                                                                                 'cannot '
                                                                                                 'edit '
                                                                                                 'it.',
 'Il salvataggio non è ancora configurato (mancano le impostazioni di salvataggio nei secrets di Streamlit). Puoi comunque provare i calcoli.': 'Saving '
                                                                                                                                                'is '
                                                                                                                                                'not '
                                                                                                                                                'configured '
                                                                                                                                                'yet '
                                                                                                                                                '(the '
                                                                                                                                                'saving '
                                                                                                                                                'settings '
                                                                                                                                                'are '
                                                                                                                                                'missing '
                                                                                                                                                'from '
                                                                                                                                                'the '
                                                                                                                                                'Streamlit '
                                                                                                                                                'secrets). '
                                                                                                                                                'You '
                                                                                                                                                'can '
                                                                                                                                                'still '
                                                                                                                                                'try '
                                                                                                                                                'the '
                                                                                                                                                'calculations.',
 '🔧 Verifica collegamento con il Google Sheet': '🔧 Check the connection with the Google Sheet',
 'Controlla, senza scrivere nulla, che lo script e il foglio siano collegati bene.': 'Checks, '
                                                                                     'without '
                                                                                     'writing '
                                                                                     'anything, '
                                                                                     'that the '
                                                                                     'script and '
                                                                                     'the sheet '
                                                                                     'are properly '
                                                                                     'connected.',
 'Esegui verifica': 'Run check',
 '➕ Nuovo esercizio…': '➕ New exercise…',
 'Nome del nuovo esercizio': 'Name of the new exercise',
 'Ripetizioni': 'Repetitions',
 'RIR (facoltativo)': 'RIR (optional)',
 'Peso corporeo (kg)': 'Body weight (kg)',
 'Serve per la forza relativa. 0 = non indicato.': 'Needed for relative strength. 0 = not '
                                                   'specified.',
 'Target forza relativa (× peso corporeo)': 'Relative strength target (× body weight)',
 'Es. 1.8 = 1RM pari a 1,8 volte il peso corporeo. 0 = nessun target.': 'E.g. 1.8 = a 1RM equal to '
                                                                        '1.8 times body weight. 0 '
                                                                        '= no target.',
 'Note (facoltativo)': 'Notes (optional)',
 '###### 🧮 Calcolo con questa serie': '###### 🧮 Calculation with this set',
 '💾 Salva serie': '💾 Save set',
 "Scrivi il nome dell'esercizio.": 'Enter the exercise name.',
 'Inserisci i kg sollevati.': 'Enter the kg lifted.',
 '###### 🕘 Ultime serie registrate per questo esercizio': '###### 🕘 Latest sets recorded for this '
                                                          'exercise',
 '##### 📈 Carichi, Massimali & Andamento per Esercizio': '##### 📈 Loads, Maxes & Trend by Exercise',
 'ℹ️ Nessuna serie registrata (o scheda non leggibile). Inserisci la prima dalla scheda **✍️ Inserisci Carichi**: la scheda «Carichi» del Google Sheet viene creata da sola al primo salvataggio.': 'ℹ️ '
                                                                                                                                                                                                    'No '
                                                                                                                                                                                                    'set '
                                                                                                                                                                                                    'recorded '
                                                                                                                                                                                                    '(or '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    'sheet '
                                                                                                                                                                                                    'is '
                                                                                                                                                                                                    'not '
                                                                                                                                                                                                    'readable). '
                                                                                                                                                                                                    'Enter '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    'first '
                                                                                                                                                                                                    'one '
                                                                                                                                                                                                    'from '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    '**✍️ '
                                                                                                                                                                                                    'Enter '
                                                                                                                                                                                                    'loads** '
                                                                                                                                                                                                    'tab: '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    '«Carichi» '
                                                                                                                                                                                                    'tab '
                                                                                                                                                                                                    'in '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    'Google '
                                                                                                                                                                                                    'Sheet '
                                                                                                                                                                                                    'is '
                                                                                                                                                                                                    'created '
                                                                                                                                                                                                    'automatically '
                                                                                                                                                                                                    'on '
                                                                                                                                                                                                    'the '
                                                                                                                                                                                                    'first '
                                                                                                                                                                                                    'save.',
 'ℹ️ Nessun carico registrato per ora.': 'ℹ️ No loads recorded yet.',
 '1RM stimato = Peso × (1 + (Reps + RIR) / 30), formula di Epley, considerato attendibile fino a 10 ripetizioni. Esempio: 120 kg × 4 → circa 136 kg.': 'Estimated '
                                                                                                                                                       '1RM '
                                                                                                                                                       '= '
                                                                                                                                                       'Weight '
                                                                                                                                                       '× '
                                                                                                                                                       '(1 '
                                                                                                                                                       '+ '
                                                                                                                                                       '(Reps '
                                                                                                                                                       '+ '
                                                                                                                                                       'RIR) '
                                                                                                                                                       '/ '
                                                                                                                                                       '30), '
                                                                                                                                                       'Epley '
                                                                                                                                                       'formula, '
                                                                                                                                                       'considered '
                                                                                                                                                       'reliable '
                                                                                                                                                       'up '
                                                                                                                                                       'to '
                                                                                                                                                       '10 '
                                                                                                                                                       'reps. '
                                                                                                                                                       'Example: '
                                                                                                                                                       '120 '
                                                                                                                                                       'kg '
                                                                                                                                                       '× '
                                                                                                                                                       '4 '
                                                                                                                                                       '→ '
                                                                                                                                                       'about '
                                                                                                                                                       '136 '
                                                                                                                                                       'kg.',
 '###### 🏆 Massimali per esercizio': '###### 🏆 Maxes by exercise',
 'Forza massima attuale: 1RM stimato (kg)': 'Current max strength: estimated 1RM (kg)',
 'Serie del 1RM': 'Set of the 1RM',
 'Data 1RM': '1RM date',
 'Forza relativa (×BW)': 'Relative strength (×BW)',
 'Target (×BW)': 'Target (×BW)',
 '1RM ideale (kg)': 'Ideal 1RM (kg)',
 '% del target': '% of target',
 'Carico max (kg)': 'Max load (kg)',
 'Serie del carico max': 'Set of the max load',
 'Ultima seduta': 'Latest session',
 'Ultima serie': 'Latest set',
 'Serie totali': 'Total sets',
 'Tonnellaggio (kg)': 'Tonnage (kg)',
 '🟠 Tacca arancione = 1RM ideale (target forza relativa × peso corporeo)': '🟠 Orange tick = ideal '
                                                                           '1RM (relative strength '
                                                                           'target × body weight)',
 'Mostra': 'Show',
 'Nessun dato disponibile per questa misura.': 'No data available for this measure.',
 'Data seduta': 'Session date',
 'Serie col carico maggiore': 'Set with the highest load',
 '📋 Tutte le serie registrate': '📋 All recorded sets',
 'Peso (kg)': 'Weight (kg)',
 '##### 🏋️\u200d♂️ Valutazione Forza & Massimali Teorici (Sincronizzato da Google Drive)': '##### '
                                                                                           '🏋️\u200d♂️ '
                                                                                           'Strength '
                                                                                           'assessment '
                                                                                           '& '
                                                                                           'theoretical '
                                                                                           'maxes '
                                                                                           '(synced '
                                                                                           'from '
                                                                                           'Google '
                                                                                           'Drive)',
 'Seleziona Esercizio di Forza:': 'Select strength exercise:',
 'Filtra per Giocatore/i:': 'Filter by player(s):',
 '1RM Teorico (kg)': 'Theoretical 1RM (kg)',
 'Forza Relativa (xBW)': 'Relative strength (xBW)',
 'ℹ️ Impossibile caricare il foglio Google di valutazione della forza.': 'ℹ️ Unable to load the '
                                                                         'Google sheet with the '
                                                                         'strength assessment.',
 '##### 🏋️\u200d♂️ Tonnellaggio Sollevato per Data e Giocatore (kg)': '##### 🏋️\u200d♂️ Tonnage '
                                                                      'lifted by date and player '
                                                                      '(kg)',
 'Data Seduta Pesi': 'Weight session date',
 'Tonnellaggio Totale (kg)': 'Total tonnage (kg)',
 'ℹ️ Nessun dato di tonnellaggio disponibile.': 'ℹ️ No tonnage data available.',
 'presente': 'present',
 'Rematore alle anelle': 'Ring Row',
 'Trazioni': 'Pull-ups',
 'Calf Rise gamba singola': 'Single-leg Calf Raise',
 'Spinte Manubri panca 30°': 'Incline Dumbbell Press 30°',
 'Spinte Manubri': 'Dumbbell Press',
 'Stacco QB': 'Trap Bar Deadlift',
 'Stacco Quadrabar': 'Trap Bar Deadlift',
 'Stacco rumeno': 'Romanian Deadlift',
 'Squat frontale': 'Front Squat',
 'Forza Massima': 'Max Strength',
 'Forza massima': 'Max Strength',
 'Forza Esplosiva': 'Explosive Strength',
 'Forza esplosiva': 'Explosive Strength',
 'Salto Max': 'Max jump',
 'Media Salti': 'Average jumps',
 'Giocatori Monitorati': 'Players monitored',
 'Data': 'Date',
 'Note': 'Notes',
 'Ruolo': 'Role',
 'Altro': 'Other',
 'Peso usato': 'Weight used',
 '1RM Teorico': 'Theoretical 1RM',
 '1RM Ideale': 'Ideal 1RM',
 'Misura': 'Measure',
 'Valore': 'Value',
 'Lun': 'Mon',
 'Mar': 'Tue',
 'Mer': 'Wed',
 'Gio': 'Thu',
 'Ven': 'Fri',
 'Sab': 'Sat',
 'Dom': 'Sun',
 '1RM teorico (Epley)': 'Theoretical 1RM (Epley)',
 'Forza massima attuale': 'Current max strength',
 'Forza relativa (× BW)': 'Relative strength (× BW)',
 'Target (1RM ideale)': 'Target (ideal 1RM)',
 'Forza massima attuale (1RM)': 'Current max strength (1RM)',
 'Target forza relativa': 'Relative strength target',
 'Target raggiunto': 'Target reached',
 'Tutte le sedute': 'All sessions',
 'Tutti gli atleti': 'All athletes',
 '🔗 Vai alla scheda ufficiale su Lega Pallavolo Serie A': '🔗 Go to the official profile on Lega '
                                                          'Pallavolo Serie A'}


EN_TEMPLATES = {"Risposta inattesa dallo script Google (codice {0}): controlla che la web app sia pubblicata con accesso «Chiunque» e che l'indirizzo finisca con /exec.": 'Unexpected '
                                                                                                                                                            'response '
                                                                                                                                                            'from '
                                                                                                                                                            'the '
                                                                                                                                                            'Google '
                                                                                                                                                            'script '
                                                                                                                                                            '(code '
                                                                                                                                                            '{0}): '
                                                                                                                                                            'check '
                                                                                                                                                            'that '
                                                                                                                                                            'the '
                                                                                                                                                            'web '
                                                                                                                                                            'app '
                                                                                                                                                            'is '
                                                                                                                                                            'published '
                                                                                                                                                            'with '
                                                                                                                                                            'access '
                                                                                                                                                            'set '
                                                                                                                                                            'to '
                                                                                                                                                            '«Anyone» '
                                                                                                                                                            'and '
                                                                                                                                                            'that '
                                                                                                                                                            'the '
                                                                                                                                                            'address '
                                                                                                                                                            'ends '
                                                                                                                                                            'with '
                                                                                                                                                            '/exec.',
 'Lo script ha rifiutato il salvataggio: {0}': 'The script refused to save: {0}',
 'Non riesco a collegarmi allo script ({0}).': "I can't connect to the script ({0}).",
 "Google risponde (codice {0}) ma non è lo script. Controlla che l'indirizzo finisca con /exec e che il deployment sia «Esegui come: Io» e «Chi ha accesso: Chiunque».": 'Google '
                                                                                                                                                                         'responds '
                                                                                                                                                                         '(code '
                                                                                                                                                                         '{0}) '
                                                                                                                                                                         'but '
                                                                                                                                                                         'it '
                                                                                                                                                                         'is '
                                                                                                                                                                         'not '
                                                                                                                                                                         'the '
                                                                                                                                                                         'script. '
                                                                                                                                                                         'Check '
                                                                                                                                                                         'that '
                                                                                                                                                                         'the '
                                                                                                                                                                         'address '
                                                                                                                                                                         'ends '
                                                                                                                                                                         'with '
                                                                                                                                                                         '/exec '
                                                                                                                                                                         'and '
                                                                                                                                                                         'that '
                                                                                                                                                                         'the '
                                                                                                                                                                         'deployment '
                                                                                                                                                                         'is '
                                                                                                                                                                         '«Execute '
                                                                                                                                                                         'as: '
                                                                                                                                                                         'Me» '
                                                                                                                                                                         'and '
                                                                                                                                                                         '«Who '
                                                                                                                                                                         'has '
                                                                                                                                                                         'access: '
                                                                                                                                                                         'Anyone».',
 'Lo script risponde ma rifiuta: {0}. Se dice «chiave non valida», apps_script_key nei secrets deve essere identica a CHIAVE nello script.': 'The '
                                                                                                                                             'script '
                                                                                                                                             'responds '
                                                                                                                                             'but '
                                                                                                                                             'refuses: '
                                                                                                                                             '{0}. '
                                                                                                                                             'If '
                                                                                                                                             'it '
                                                                                                                                             'says '
                                                                                                                                             '«chiave '
                                                                                                                                             'non '
                                                                                                                                             'valida» '
                                                                                                                                             '(invalid '
                                                                                                                                             'key), '
                                                                                                                                             'apps_script_key '
                                                                                                                                             'in '
                                                                                                                                             'the '
                                                                                                                                             'secrets '
                                                                                                                                             'must '
                                                                                                                                             'be '
                                                                                                                                             'identical '
                                                                                                                                             'to '
                                                                                                                                             'CHIAVE '
                                                                                                                                             'in '
                                                                                                                                             'the '
                                                                                                                                             'script.',
 'Lo script funziona, ma scrive nel file «{0}» (ID {1}) mentre l\'app legge un altro file (ID {2}). Nei secrets scrivi: sheet_id = "{3}"': 'The '
                                                                                                                                           'script '
                                                                                                                                           'works, '
                                                                                                                                           'but '
                                                                                                                                           'it '
                                                                                                                                           'writes '
                                                                                                                                           'to '
                                                                                                                                           'the '
                                                                                                                                           'file '
                                                                                                                                           '«{0}» '
                                                                                                                                           '(ID '
                                                                                                                                           '{1}) '
                                                                                                                                           'while '
                                                                                                                                           'the '
                                                                                                                                           'app '
                                                                                                                                           'reads '
                                                                                                                                           'another '
                                                                                                                                           'file '
                                                                                                                                           '(ID '
                                                                                                                                           '{2}). '
                                                                                                                                           'In '
                                                                                                                                           'the '
                                                                                                                                           'secrets '
                                                                                                                                           'write: '
                                                                                                                                           'sheet_id '
                                                                                                                                           '= '
                                                                                                                                           '"{3}"',
 "Lo script funziona e scrive nel file «{0}», lo stesso che legge l'app. Scheda «Carichi»: {1}.": 'The '
                                                                                                  'script '
                                                                                                  'works '
                                                                                                  'and '
                                                                                                  'writes '
                                                                                                  'to '
                                                                                                  'the '
                                                                                                  'file '
                                                                                                  '«{0}», '
                                                                                                  'the '
                                                                                                  'same '
                                                                                                  'one '
                                                                                                  'the '
                                                                                                  'app '
                                                                                                  'reads. '
                                                                                                  '«Carichi» '
                                                                                                  'tab: '
                                                                                                  '{1}.',
 'Non riesco a collegarmi a Google ({0}).': "I can't connect to Google ({0}).",
 "L'app non riesce a leggere il file (ID {0}, codice {1}). In Google Sheet: Condividi → Accesso generale → «Chiunque abbia il link» → ruolo «Visualizzatore». Controlla anche che sheet_id nei secrets sia l'ID giusto.": 'The '
                                                                                                                                                                                                                          'app '
                                                                                                                                                                                                                          "can't "
                                                                                                                                                                                                                          'read '
                                                                                                                                                                                                                          'the '
                                                                                                                                                                                                                          'file '
                                                                                                                                                                                                                          '(ID '
                                                                                                                                                                                                                          '{0}, '
                                                                                                                                                                                                                          'code '
                                                                                                                                                                                                                          '{1}). '
                                                                                                                                                                                                                          'In '
                                                                                                                                                                                                                          'Google '
                                                                                                                                                                                                                          'Sheets: '
                                                                                                                                                                                                                          'Share '
                                                                                                                                                                                                                          '→ '
                                                                                                                                                                                                                          'General '
                                                                                                                                                                                                                          'access '
                                                                                                                                                                                                                          '→ '
                                                                                                                                                                                                                          '«Anyone '
                                                                                                                                                                                                                          'with '
                                                                                                                                                                                                                          'the '
                                                                                                                                                                                                                          'link» '
                                                                                                                                                                                                                          '→ '
                                                                                                                                                                                                                          'role '
                                                                                                                                                                                                                          '«Viewer». '
                                                                                                                                                                                                                          'Also '
                                                                                                                                                                                                                          'check '
                                                                                                                                                                                                                          'that '
                                                                                                                                                                                                                          'sheet_id '
                                                                                                                                                                                                                          'in '
                                                                                                                                                                                                                          'the '
                                                                                                                                                                                                                          'secrets '
                                                                                                                                                                                                                          'is '
                                                                                                                                                                                                                          'the '
                                                                                                                                                                                                                          'right '
                                                                                                                                                                                                                          'ID.',
 "L'app legge il file (ID {0}).": 'The app reads the file (ID {0}).',
 'Google non restituisce i dati (codice {0}). Controlla che il foglio sia condiviso come «Chiunque abbia il link: Visualizzatore».': 'Google '
                                                                                                                                     'does '
                                                                                                                                     'not '
                                                                                                                                     'return '
                                                                                                                                     'the '
                                                                                                                                     'data '
                                                                                                                                     '(code '
                                                                                                                                     '{0}). '
                                                                                                                                     'Check '
                                                                                                                                     'that '
                                                                                                                                     'the '
                                                                                                                                     'sheet '
                                                                                                                                     'is '
                                                                                                                                     'shared '
                                                                                                                                     'as '
                                                                                                                                     '«Anyone '
                                                                                                                                     'with '
                                                                                                                                     'the '
                                                                                                                                     'link: '
                                                                                                                                     'Viewer».',
 'Il foglio risponde ma non riesco a leggerlo ({0}).': "The sheet responds but I can't read it "
                                                       '({0}).',
 'Il foglio risponde con {0} righe e queste colonne: {1}. Mancano: {2}. Se queste colonne non sono quelle di Carichi, la scheda «Carichi» non esiste in questo foglio (Google mostra la prima scheda al suo posto) oppure le intestazioni non sono nella riga 1.': 'The '
                                                                                                                                                                                                                                                                   'sheet '
                                                                                                                                                                                                                                                                   'responds '
                                                                                                                                                                                                                                                                   'with '
                                                                                                                                                                                                                                                                   '{0} '
                                                                                                                                                                                                                                                                   'rows '
                                                                                                                                                                                                                                                                   'and '
                                                                                                                                                                                                                                                                   'these '
                                                                                                                                                                                                                                                                   'columns: '
                                                                                                                                                                                                                                                                   '{1}. '
                                                                                                                                                                                                                                                                   'Missing: '
                                                                                                                                                                                                                                                                   '{2}. '
                                                                                                                                                                                                                                                                   'If '
                                                                                                                                                                                                                                                                   'these '
                                                                                                                                                                                                                                                                   'columns '
                                                                                                                                                                                                                                                                   'are '
                                                                                                                                                                                                                                                                   'not '
                                                                                                                                                                                                                                                                   'those '
                                                                                                                                                                                                                                                                   'of '
                                                                                                                                                                                                                                                                   'Carichi, '
                                                                                                                                                                                                                                                                   'the '
                                                                                                                                                                                                                                                                   '«Carichi» '
                                                                                                                                                                                                                                                                   'tab '
                                                                                                                                                                                                                                                                   'does '
                                                                                                                                                                                                                                                                   'not '
                                                                                                                                                                                                                                                                   'exist '
                                                                                                                                                                                                                                                                   'in '
                                                                                                                                                                                                                                                                   'this '
                                                                                                                                                                                                                                                                   'sheet '
                                                                                                                                                                                                                                                                   '(Google '
                                                                                                                                                                                                                                                                   'shows '
                                                                                                                                                                                                                                                                   'the '
                                                                                                                                                                                                                                                                   'first '
                                                                                                                                                                                                                                                                   'tab '
                                                                                                                                                                                                                                                                   'instead) '
                                                                                                                                                                                                                                                                   'or '
                                                                                                                                                                                                                                                                   'the '
                                                                                                                                                                                                                                                                   'headers '
                                                                                                                                                                                                                                                                   'are '
                                                                                                                                                                                                                                                                   'not '
                                                                                                                                                                                                                                                                   'in '
                                                                                                                                                                                                                                                                   'row '
                                                                                                                                                                                                                                                                   '1.',
 'Le colonne sono corrette ({0} righe), ma nessuna riga è valida: controlla che Data sia una data (es. 2026-10-20) e che Peso e Reps siano numeri maggiori di 0.': 'The '
                                                                                                                                                                   'columns '
                                                                                                                                                                   'are '
                                                                                                                                                                   'correct '
                                                                                                                                                                   '({0} '
                                                                                                                                                                   'rows), '
                                                                                                                                                                   'but '
                                                                                                                                                                   'no '
                                                                                                                                                                   'row '
                                                                                                                                                                   'is '
                                                                                                                                                                   'valid: '
                                                                                                                                                                   'check '
                                                                                                                                                                   'that '
                                                                                                                                                                   'Date '
                                                                                                                                                                   'is '
                                                                                                                                                                   'a '
                                                                                                                                                                   'date '
                                                                                                                                                                   '(e.g. '
                                                                                                                                                                   '2026-10-20) '
                                                                                                                                                                   'and '
                                                                                                                                                                   'that '
                                                                                                                                                                   'Weight '
                                                                                                                                                                   'and '
                                                                                                                                                                   'Reps '
                                                                                                                                                                   'are '
                                                                                                                                                                   'numbers '
                                                                                                                                                                   'greater '
                                                                                                                                                                   'than '
                                                                                                                                                                   '0.',
 'codice {0}: il file non è condiviso come «Chiunque abbia il link → Visualizzatore» oppure non è un Google Sheet': 'code '
                                                                                                                    '{0}: '
                                                                                                                    'the '
                                                                                                                    'file '
                                                                                                                    'is '
                                                                                                                    'not '
                                                                                                                    'shared '
                                                                                                                    'as '
                                                                                                                    '«Anyone '
                                                                                                                    'with '
                                                                                                                    'the '
                                                                                                                    'link '
                                                                                                                    '→ '
                                                                                                                    'Viewer» '
                                                                                                                    'or '
                                                                                                                    'it '
                                                                                                                    'is '
                                                                                                                    'not '
                                                                                                                    'a '
                                                                                                                    'Google '
                                                                                                                    'Sheet',
 'cartella {0}…: {1} elementi trovati': 'folder {0}…: {1} items found',
 '🔓 Visualizzazione Dedicata: {0}': '🔓 Dedicated view: {0}',
 '📁 {0} file CSV trovati · {1} sedute caricate': '📁 {0} CSV files found · {1} sessions loaded',
 "##### 📈 Andamento dei Salti all'Interno delle Sessioni — {0}": '##### 📈 Jump trend within the '
                                                                 'sessions — {0}',
 '**📅 Seduta del: {0}**': '**📅 Session of: {0}**',
 'Totale Salti — {0}': 'Total jumps — {0}',
 'Salto Max — {0}': 'Max jump — {0}',
 'Media Salti — {0}': 'Average jumps — {0}',
 'Sedute — {0}': 'Sessions — {0}',
 '{0}: {1} salti · max {2} cm · media {3} cm · {4} sedute': '{0}: {1} jumps · max {2} cm · avg {3} '
                                                            'cm · {4} sessions',
 'Salti {0}': 'Jumps {0}',
 'Media {0} (cm)': 'Avg {0} (cm)',
 'Max {0} (cm)': 'Max {0} (cm)',
 '{0} file da leggere.': '{0} files to read.',
 '{0} file, {1} schede: {2} lette, {3} con avvisi.': '{0} files, {1} sheets: {2} read, {3} with '
                                                     'warnings.',
 '###### 🗓️ Scheda di {0} — {1}': '###### 🗓️ Plan of {0} — {1}',
 '###### 🏆 Massimali di {0} (tutte le settimane)': '###### 🏆 Maxes of {0} (all weeks)',
 '###### 📈 Andamento di {0} per esercizio': '###### 📈 Trend of {0} by exercise',
 'Scrittura: {0}': 'Writing: {0}',
 'Lettura: {0}': 'Reading: {0}',
 '{0}% raggiunto': '{0}% reached',
 '1RM = {0} × (1 + ({1} + {2}) / 30). Con più di 10 ripetizioni (RIR compreso) la stima non è affidabile e la serie non entra nella forza massima.': '1RM '
                                                                                                                                                     '= '
                                                                                                                                                     '{0} '
                                                                                                                                                     '× '
                                                                                                                                                     '(1 '
                                                                                                                                                     '+ '
                                                                                                                                                     '({1} '
                                                                                                                                                     '+ '
                                                                                                                                                     '{2}) '
                                                                                                                                                     '/ '
                                                                                                                                                     '30). '
                                                                                                                                                     'With '
                                                                                                                                                     'more '
                                                                                                                                                     'than '
                                                                                                                                                     '10 '
                                                                                                                                                     'reps '
                                                                                                                                                     '(RIR '
                                                                                                                                                     'included) '
                                                                                                                                                     'the '
                                                                                                                                                     'estimate '
                                                                                                                                                     'is '
                                                                                                                                                     'not '
                                                                                                                                                     'reliable '
                                                                                                                                                     'and '
                                                                                                                                                     'the '
                                                                                                                                                     'set '
                                                                                                                                                     'does '
                                                                                                                                                     'not '
                                                                                                                                                     'count '
                                                                                                                                                     'towards '
                                                                                                                                                     'max '
                                                                                                                                                     'strength.',
 '✅ Salvato: {0} — {1}, {2} kg × {3} (1RM stimato {4} kg)': '✅ Saved: {0} — {1}, {2} kg × {3} '
                                                            '(estimated 1RM {4} kg)',
 'Non sono riuscito a salvare ({0}): {1}': "I couldn't save ({0}): {1}",
 '🔎 Diagnosi: {0}': '🔎 Diagnosis: {0}',
 '1RM stimato (kg) — {0}': 'Estimated 1RM (kg) — {0}',
 '###### 📈 Andamento — {0}': '###### 📈 Trend — {0}',
 '**1RM Teorico (kg) — {0}**': '**Theoretical 1RM (kg) — {0}**',
 '**Forza Relativa (1RM / BW) — {0}**': '**Relative strength (1RM / BW) — {0}**',
 '**{0}**': '**{0}**',
 '**1RM stimato (kg) — {0}**': '**Estimated 1RM (kg) — {0}**',
 '{0} vs {1}': '{0} vs {1}',
 'Week {0} — {1}': 'Week {0} — {1}',
 'Settimana {0}': 'Week {0}',
 '{0} | Altezza: {1} cm | Classe {2}': '{0} | Height: {1} cm | Class of {2}',
 '**📅 Seduta del: {0}** &nbsp; 🟠 **Match day**': '**📅 Session of: {0}** &nbsp; 🟠 **Match day**'}


def current_lang():
  try:
    return _st_real.session_state.get("lang", "it")
  except Exception:
    return "it"


_TEMPLATES = []


def _compiled_templates():
  if not _TEMPLATES:
    for it_text, en_text in EN_TEMPLATES.items():
      parts = re.split(r"\{(\d+)\}", it_text)
      rx = "".join(
          re.escape(p) if i % 2 == 0 else "(.+?)" for i, p in enumerate(parts)
      )
      idx = [int(p) for i, p in enumerate(parts) if i % 2 == 1]
      _TEMPLATES.append((re.compile("^" + rx + "$", re.S), idx, en_text))
    _TEMPLATES.sort(key=lambda t: -len(t[0].pattern))
  return _TEMPLATES


def T(text, _depth=0):
  """Traduce un testo in inglese (solo se la lingua scelta è l'inglese)."""
  if not isinstance(text, str) or current_lang() != "en":
    return text
  hit = EN_STATIC.get(text)
  if hit is not None:
    return hit
  if _depth < 2:
    for rx, idx, en_text in _compiled_templates():
      m = rx.match(text)
      if m:
        vals = {i: T(m.group(k + 1), _depth + 1) for k, i in enumerate(idx)}
        try:
          return en_text.format(*[vals.get(i, "") for i in range(max(vals) + 1)])
        except Exception:
          return text
  return text


def _t_cell(v):
  """Traduzione di un valore in tabella o nei dati di un grafico (solo frasi note)."""
  if isinstance(v, str):
    if v in EN_STATIC:
      return EN_STATIC[v]
    if v.startswith("Settimana "):
      return "Week " + v[len("Settimana "):]
  return v


def _translate_df(df):
  cols = []
  for i in range(df.shape[1]):
    s = df.iloc[:, i]
    is_text = s.dtype == object or pd.api.types.is_string_dtype(s.dtype)
    cols.append(s.map(_t_cell) if is_text else s)
  out = pd.concat(cols, axis=1)
  out.columns = [T(c) if isinstance(c, str) else c for c in df.columns]
  return out


def _translate_spec(node, in_enc=False):
  """Traduce titoli, etichette e dati testuali di un grafico Vega-Lite."""
  if isinstance(node, dict):
    out = {}
    # un campo senza titolo mostra il nome della colonna: se lo conosco, lo traduco
    if in_enc and isinstance(node.get("field"), str) and "title" not in node:
      t = T(node["field"])
      if t != node["field"]:
        out["title"] = t
    for k, v in node.items():
      if k == "title" and isinstance(v, str):
        out[k] = T(v)
      elif k == "title" and isinstance(v, list):
        out[k] = [T(x) if isinstance(x, str) else x for x in v]
      elif k in ("sort", "domain") and isinstance(v, list):
        out[k] = [_t_cell(x) if isinstance(x, str) else x for x in v]
      elif k == "datasets" and isinstance(v, dict):
        out[k] = {
            name: [
                {fk: _t_cell(fv) for fk, fv in row.items()}
                if isinstance(row, dict)
                else row
                for row in rows
            ]
            for name, rows in v.items()
        }
      else:
        out[k] = _translate_spec(v, in_enc or k == "encoding")
    return out
  if isinstance(node, list):
    return [_translate_spec(x, in_enc) for x in node]
  return node


_TEXT_FUNCS = {
    "markdown", "caption", "info", "warning", "error", "success", "write",
    "header", "subheader", "title", "toast",
}


_WIDGET_FUNCS = {
    "selectbox", "multiselect", "radio", "number_input", "text_input",
    "date_input", "button", "expander", "checkbox", "toggle", "slider",
    "metric", "text_area",
}


_CHOICE_FUNCS = {"selectbox", "multiselect", "radio"}


class _I18n:
  """Avvolge streamlit: in inglese traduce testi, etichette, tabelle e grafici."""

  def __init__(self, target):
    self._target = target

  def __enter__(self):
    return self._target.__enter__()

  def __exit__(self, *args):
    return self._target.__exit__(*args)

  def __getattr__(self, name):
    attr = getattr(self._target, name)
    if name == "sidebar":
      return _I18n(attr)
    if not callable(attr):
      return attr

    if name in _TEXT_FUNCS:
      def text_fn(body=None, *args, **kwargs):
        if current_lang() == "en":
          if isinstance(body, str) and not kwargs.get("unsafe_allow_html"):
            body = T(body)
          if isinstance(kwargs.get("help"), str):
            kwargs["help"] = T(kwargs["help"])
        return attr(body, *args, **kwargs)
      return text_fn

    if name in _WIDGET_FUNCS:
      def widget_fn(label=None, *args, **kwargs):
        if current_lang() == "en":
          if isinstance(label, str):
            label = T(label)
          for k in ("help", "placeholder", "delta"):
            if isinstance(kwargs.get(k), str):
              kwargs[k] = T(kwargs[k])
          if name == "metric" and len(args) >= 2 and isinstance(args[1], str):
            args = (args[0], T(args[1])) + tuple(args[2:])
          if name in _CHOICE_FUNCS:
            user_ff = kwargs.get("format_func")

            def ff(v, _u=user_ff):
              s = _u(v) if _u else (v if isinstance(v, str) else str(v))
              return T(s) if isinstance(s, str) else s

            kwargs["format_func"] = ff
        return attr(label, *args, **kwargs)
      return widget_fn

    if name == "tabs":
      def tabs_fn(labels, *args, **kwargs):
        if current_lang() == "en":
          labels = [T(x) if isinstance(x, str) else x for x in labels]
        return [_I18n(t) for t in attr(labels, *args, **kwargs)]
      return tabs_fn

    if name == "columns":
      def columns_fn(*args, **kwargs):
        return [_I18n(c) for c in attr(*args, **kwargs)]
      return columns_fn

    if name == "dataframe":
      def dataframe_fn(data=None, *args, **kwargs):
        if current_lang() == "en" and isinstance(data, pd.DataFrame):
          try:
            data = _translate_df(data)
          except Exception:
            pass
        return attr(data, *args, **kwargs)
      return dataframe_fn

    if name == "altair_chart":
      def altair_fn(chart, *args, **kwargs):
        if current_lang() == "en":
          try:
            with alt.data_transformers.enable("default", max_rows=None):
              spec = chart.to_dict()
            return self._target.vega_lite_chart(
                spec=_translate_spec(spec), **kwargs
            )
          except Exception:
            pass
        return attr(chart, *args, **kwargs)
      return altair_fn

    return attr


st = _I18n(_st_real)


# CSS personalizzato dell'app (grafica): modifica qui i colori e gli stili
STYLE_HTML = """
    <head>
        <link rel="apple-touch-icon" href="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10">
        <link rel="shortcut icon" href="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrtebVKDZUcg5g5UGl6FaaJFeAsNY8i6YtrvdbHcHrAw&s=10">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="theme-color" content="#2563eb">
    </head>
    
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    button[data-testid="stHeaderIconButton"] {
        visibility: visible !important;
        display: block !important;
    }

    .stApp {
        background-color: #ffffff;
        color: #1f2937;
    }

    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-size: 0.95rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #2563eb !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }

    .player-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
    }
    .player-title {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .player-role {
        color: #2563eb;
        font-size: 1.1rem;
        font-weight: 700;
    }

    div.stButton > button {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 35px 20px !important;
        height: auto !important;
        width: 100% !important;
        box-shadow: 0px 6px 16px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease-in-out !important;
        white-space: pre-wrap !important;
        line-height: 1.5 !important;
    }
    
    div.stButton > button:hover {
        border-color: #2563eb !important;
        background-color: #ffffff !important;
        box-shadow: 0px 10px 24px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-4px) !important;
    }

    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
"""



def setup_app():
  """Da chiamare a ogni esecuzione: pagina, grafica, lingua, sessione e parametri URL.

  Restituisce 'ALL' oppure la lista con l'atleta indicato nel link (?atleta=...).
  """
  _st_real.set_page_config(
      page_title="Cuneo Volley Performance Hub",
      page_icon="🛡️",
      layout="wide",
      initial_sidebar_state="expanded",
  )

  # 2. CSS Personalizzato (stesso identico codice HTML/CSS di prima)
  st.markdown(STYLE_HTML, unsafe_allow_html=True)

  # 2b. Lingua: ?lang=en nel link oppure il selettore in cima alla barra laterale
  if "lang" not in st.session_state:
    _q = st.query_params.get("lang", "it")
    if isinstance(_q, list):
      _q = _q[0] if _q else "it"
    st.session_state.lang = "en" if str(_q).lower().startswith("en") else "it"

  _lang_choice = _st_real.sidebar.radio(
      "🌐 Lingua / Language",
      ["Italiano", "English"],
      index=1 if st.session_state.lang == "en" else 0,
      horizontal=True,
      key="lang_choice",
  )
  _new_lang = "en" if _lang_choice == "English" else "it"
  if _new_lang != st.session_state.lang:
    st.session_state.lang = _new_lang
    st.query_params["lang"] = _new_lang
    st.rerun()

  # 3. Inizializzazione Sessione e Gestione Parametri URL
  if "page" not in st.session_state:
    st.session_state.page = "home"

  # Lettura robusta del parametro dall'URL
  query_params = st.query_params
  url_athlete = query_params.get("atleta", None)

  if isinstance(url_athlete, list):
    url_athlete = url_athlete[0] if url_athlete else None

  if url_athlete:
    allowed_athletes = [url_athlete]
  else:
    allowed_athletes = "ALL"

  return allowed_athletes



ruoli_dict = {
    "Bryan Argilagos": "Palleggiatore",
    "Manuel Coscione": "Palleggiatore",
    "Alexandre Strehlau": "Schiacciatore",
    "Ethan Champlin": "Schiacciatore",
    "Federico Giraudo": "Schiacciatore",
    "Poriya Khanzadeh": "Schiacciatore",
    "Nathan Feral": "Opposto",
    "Lorenzo Sala": "Opposto",
    "Emanuele Barberio": "Centrale",
    "Leandro Mosca": "Centrale",
    "Lorenzo Codarin": "Centrale",
    "Nicoló Volpe": "Centrale",
    "Mimmo Cavaccini": "Libero",
    "Thibault Loubeyre": "Libero",
}


cognomi_to_full = {
    "Argilagos": "Bryan Argilagos",
    "Coscione": "Manuel Coscione",
    "Strehlau": "Alexandre Strehlau",
    "Champlin": "Ethan Champlin",
    "Giraudo": "Federico Giraudo",
    "Poriya": "Poriya Khanzadeh",
    "Feral": "Nathan Feral",
    "Sala": "Lorenzo Sala",
    "Barberio": "Emanuele Barberio",
    "Mosca": "Leandro Mosca",
    "Codarin": "Lorenzo Codarin",
    "Volpe": "Nicoló Volpe",
    "Cavaccini": "Mimmo Cavaccini",
    "Loubeyre": "Thibault Loubeyre",
}


player_info = {
    "Bryan Argilagos": {
        "bio": "Palleggiatore | Altezza: 200 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Manuel Coscione": {
        "bio": "Palleggiatore | Altezza: 188 cm | Classe 1980",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Alexandre Strehlau": {
        "bio": "Schiacciatore | Altezza: 199 cm | Classe 2004",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Ethan Champlin": {
        "bio": "Schiacciatore | Altezza: 191 cm | Classe 2001",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Federico Giraudo": {
        "bio": "Schiacciatore | Altezza: 198 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Poriya Khanzadeh": {
        "bio": "Schiacciatore | Altezza: 202 cm | Classe 2004",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Nathan Feral": {
        "bio": "Opposto | Altezza: 197 cm | Classe 2003",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Lorenzo Sala": {
        "bio": "Opposto | Altezza: 200 cm | Classe 2002",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Emanuele Barberio": {
        "bio": "Centrale | Altezza: 202 cm | Classe 2007",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Leandro Mosca": {
        "bio": "Centrale | Altezza: 209 cm | Classe 2000",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Lorenzo Codarin": {
        "bio": "Centrale | Altezza: 199 cm | Classe 1996",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
    "Nicoló Volpe": {
        "bio": "Centrale | Altezza: 193 cm | Classe 2003",
        "url": "https://cuneovolley.it/prima-squadra/giocatori",
    },
}


MATCH_DAYS = {
    "2026-10-18",
    "2026-10-25",
    "2026-11-01",
    "2026-11-04",
    "2026-11-08",
    "2026-11-20",
    "2026-11-29",
    "2026-12-02",
    "2026-12-06",
    "2026-12-13",
    "2026-12-20",
    "2026-12-26",
    "2027-01-03",
    "2027-01-10",
    "2027-01-13",
    "2027-01-17",
    "2027-01-24",
    "2027-01-31",
    "2027-02-14",
    "2027-02-21",
    "2027-02-24",
    "2027-02-28",
}


ANCHOR_MONDAY = pd.to_datetime("2026-10-05")


# Nomi possibili della colonna con l'orario, se nei CSV è separata dalla data
TIME_COLUMNS = {"TIME", "ORA", "ORARIO", "HOUR"}


GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


BAND_ORDER = [
    "JUMPS < 30",
    "JUMPS 30-50",
    "JUMPS 50-60",
    "JUMPS 60-70",
    "JUMPS > 70",
]


REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Cuneo Volley Performance Hub)"}


def _ascii_lower(text):
  text = unicodedata.normalize("NFKD", str(text))
  return text.encode("ascii", "ignore").decode().lower()


def _slug(text):
  return re.sub(r"[^a-z]", "", _ascii_lower(text))


def _tokens(text):
  return {t for t in re.split(r"[^a-z]+", _ascii_lower(text)) if t}


# cognome normalizzato -> nome completo usato nell'app
SURNAME_TO_PLAYER = {_slug(n.split()[-1]): n for n in ruoli_dict}


def _fetch_html(url, timeout=10):
  try:
    r = requests.get(url, headers=REQ_HEADERS, timeout=timeout)
    if r.status_code == 200:
      return r.text
  except Exception:
    pass
  return ""


def get_custom_week(dt_series):
  days_diff = (dt_series.dt.normalize() - ANCHOR_MONDAY).dt.days
  week_offset = days_diff // 7
  return "Settimana " + (7 + week_offset).astype(int).astype(str)


def get_csv_files():
  files = (
      glob.glob("data/*.csv")
      + glob.glob("data/*.CSV")
      + glob.glob("*.csv")
      + glob.glob("*.CSV")
  )
  return sorted(set(files))


def get_files_signature():
  """Elenco dei CSV con data di modifica e dimensione.

  Viene passato alle funzioni di caricamento: se aggiungi o modifichi un file
  la firma cambia e la cache viene ricalcolata in automatico.
  """
  sig = []
  for f in get_csv_files():
    try:
      sig.append((f, os.path.getmtime(f), os.path.getsize(f)))
    except OSError:
      pass
  return tuple(sig)


# Controllo automatico dei file: ogni 30 secondi verifica se i CSV sono
# cambiati (nuovi file o file modificati) e, in caso, riesegue tutta l'app.
@st.fragment(run_every=30)
def watch_data_folder():
  current = get_files_signature()
  if "files_sig" not in st.session_state:
    st.session_state.files_sig = current
  elif st.session_state.files_sig != current:
    st.session_state.files_sig = current
    st.rerun()


# Rende disponibili a tutte le sezioni (anche i nomi che iniziano con _)
__all__ = [n for n in dir() if not n.startswith("__")]

