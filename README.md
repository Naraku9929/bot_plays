# Twitch AI Co-Host MVP

## Overview

This project is the Minimum Viable Product (MVP) for a Twitch AI Co-Host bot. In its current state, the bot connects to a specified Twitch channel, can capture audio from a microphone, take screenshots of the primary monitor, logs its activities and errors, and is configurable via an external `config.ini` file. It also includes basic commands for the broadcaster to control these captures and view configurations, as well as feedback mechanisms.

## Features (MVP)

*   **Twitch Chat Integration:** Connects to Twitch chat, processes messages, and recognizes commands.
*   **Configuration System:** External configuration via `config.ini` for Twitch connection details, bot personality, and operational rules. A template is generated if the file is missing.
*   **Microphone Audio Recording:**
    *   `!startaudio`: Broadcaster command to start recording audio from the default microphone.
    *   `!stopaudio`: Broadcaster command to stop recording and save the audio as a WAV file in the `recordings/` directory.
*   **Screen Capture:**
    *   `!screenshot`: Broadcaster command to capture the primary monitor and save it as a PNG file in the `screenshots/` directory.
*   **Comprehensive Logging:**
    *   Activities, errors, chat messages, and command invocations are logged to both the console and a file (`logs/bot_activity.log`).
*   **Host Feedback Commands:**
    *   `!goodbotresponse`: Allows the host/user to mark a recent bot interaction as good, logging the context.
    *   `!badbotresponse [optional reason]`: Allows the host/user to mark a recent interaction as bad, logging the context and reason.
*   **Configuration Display:**
    *   `!showconfig`: Broadcaster command to display the current Twitch, Personality, and Rules configurations in chat.

## Setup Instructions

### Prerequisites

*   **Python 3.x** (Python 3.7 or newer recommended).
*   **PortAudio Library:** `sounddevice` (used for audio recording) relies on PortAudio.
    *   On Debian/Ubuntu: `sudo apt-get install libportaudio2`
    *   On Fedora: `sudo dnf install portaudio-devel`
    *   On macOS (using Homebrew): `brew install portaudio`
    *   Windows users typically do not need to install PortAudio separately if microphone drivers are correctly installed.
*   **X11 Libraries (Linux for `mss` screen capture):**
    *   `mss` may require X11 libraries. On Debian/Ubuntu, you might need: `sudo apt-get install libxrandr-dev libxinerama-dev libxfixes-dev libxcursor-dev libxi-dev`

### Installation

1.  **Clone the Repository (or Download Files):**
    ```bash
    # If using Git
    git clone <repository_url>
    cd <repository_directory>
    ```
    Alternatively, download the project files (`twitch_chat_bot.py`, `audio_input.py`, `screen_capture.py`) into a single directory.

2.  **Create a Python Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    Ensure `requirements.txt` is in your project directory.
    ```bash
    pip install -r requirements.txt
    ```

### Configuration (`config.ini`)

1.  **Initial Run & Template Creation:**
    *   On the first run of `python twitch_chat_bot.py`, if `config.ini` is not found, the bot will automatically create a template file named `config.ini` (previously it was `config.ini.template`, but the current code directly creates `config.ini` as a template).
    *   **Important:** You MUST edit this `config.ini` file with your specific details.

2.  **[Twitch] Section:**
    *   `token`: Your Twitch OAuth token.
        *   **How to get one:** Go to a site like [Twitch Token Generator](https://twitchtokengenerator.com/). Use the "Bot Chat Token" option. The token will start with `oauth:`.
        *   **Security:** Treat this token like a password. Do NOT share it publicly or commit it to version control if your repository is public.
    *   `prefix`: The prefix for bot commands (e.g., `!`). Defaults to `!` if not set.
    *   `channel`: The name of the Twitch channel you want the bot to join (e.g., `your_twitch_username`).

3.  **[Personality] Section:**
    *   `description`: A text field where you can describe the desired personality of your AI (e.g., "A friendly and witty assistant.", "A helpful bot focused on game lore."). This will be used by the LLM in future integrations.

4.  **[Rules] Section:**
    *   This section defines operational rules for the bot (primarily for future LLM interaction).
    *   `avoid_politics` (true/false): Example rule to guide AI responses.
    *   `max_response_length` (integer): Example rule for maximum length of AI-generated messages.
    *   `custom_greeting` (string): Example rule for a specific greeting message.
    *   You can add other custom rules here; they will be loaded as strings.

## Running the Bot

Once configured, run the bot from your terminal (ensure your virtual environment is active):

```bash
python twitch_chat_bot.py
```

The bot will attempt to connect to Twitch and join the specified channel. You should see log messages in the console and in the `logs/bot_activity.log` file.

## Available Twitch Commands

All commands below are broadcaster-only by default, except for `!hello`, `!goodbotresponse`, and `!badbotresponse` which can be used by any user.

*   **`!screenshot`**: (Broadcaster Only) Takes a screenshot of the primary monitor and saves it to the `screenshots/` directory.
*   **`!startaudio`**: (Broadcaster Only) Starts recording audio from the default microphone. Saves to the `recordings/` directory.
*   **`!stopaudio`**: (Broadcaster Only) Stops the current audio recording and saves the file.
*   **`!showconfig`**: (Broadcaster Only) Displays the bot's current Twitch, Personality, and Rules configurations in the chat (chunked for readability).
*   **`!goodbotresponse`**: (All Users) Marks a recent bot interaction as "good." This is logged for feedback.
*   **`!badbotresponse [optional reason]`**: (All Users) Marks a recent bot interaction as "bad," optionally with a reason. This is logged for feedback.
*   **`!hello`**: (All Users) A simple test command; the bot replies with "Hello [username]!".

## Project Structure

```
.
├── twitch_chat_bot.py      # Main bot script, handles Twitch connection, commands, and integrations.
├── audio_input.py          # Module for microphone audio recording (AudioRecorder class).
├── screen_capture.py       # Module for screen capture (ScreenCapture class).
├── config.ini              # Configuration file (user-created from template on first run).
├── requirements.txt        # Python dependencies.
├── logs/                     # Directory for log files (e.g., bot_activity.log). Created automatically.
├── recordings/             # Default directory for saved audio WAV files. Created automatically by audio_input.py.
├── screenshots/            # Default directory for saved PNG screenshots. Created automatically by screen_capture.py.
└── README.md               # This file.
```

## Future Work

*   **LLM Integration:** Connect the bot to a Large Language Model (e.g., via OpenAI API, local models) to generate dynamic responses based on chat, personality, and rules.
*   **Contextual Awareness:** Improve the bot's understanding of ongoing conversation in Twitch chat.
*   **Advanced Command Handling:** More sophisticated command parsing and response generation.
*   **Event Handling:** Respond to other Twitch events like follows, subscriptions, raids.
*   **Web UI:** A simple web interface for easier configuration and monitoring.
*   **Modular AI Behavior:** Allow easier swapping of different AI "brains" or personalities.
```
