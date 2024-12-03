#include <Arduino.h>

bool gameActive = false;
String playerChoices[3] = {"Rock", "Paper", "Scissors"};
int gameMode = 0;

/**
 * @brief Represents the game configuration structure.
 * 
 * Contains the current game mode and player choices for the game.
 */
struct GameConfig {
  int gameMode; /**< Current game mode (0: Human vs AI, 1: Human vs Human, 2: AI vs AI) */
  String playerChoices[3]; /**< Array of player choices: Rock, Paper, Scissors */
};

/**
 * @brief Converts the game configuration into an INI-style string.
 * 
 * @param config The game configuration structure to save.
 * @return A string representation of the configuration in INI format.
 */
String saveConfig(const GameConfig &config) {
  String iniConfig;
  
  iniConfig += "gameMode=" + String(config.gameMode) + " ";
  iniConfig += "playerChoices1=" + config.playerChoices[0] + " ";
  iniConfig += "playerChoices2=" + config.playerChoices[1] + " ";
  iniConfig += "playerChoices3=" + config.playerChoices[2] + " ";
  
  Serial.println(iniConfig);
  return iniConfig;
}

/**
 * @brief Parses a single line of configuration in INI format.
 * 
 * @param line The configuration line to parse.
 * @param gameMode The game mode to be updated.
 * @param playerChoices Array of player choices to be updated.
 * @return True if the line is parsed successfully, false otherwise.
 */
bool parseConfigLine(const String &line, int &gameMode, String playerChoices[]) {
  int keyEnd = line.indexOf('=');
  if (keyEnd == -1) return false;

  String key = line.substring(0, keyEnd);
  String value = line.substring(keyEnd + 1);
  key.trim();
  value.trim();

  if (key == "gameMode") {
    gameMode = value.toInt();
  } else if (key == "playerChoices1") {
    playerChoices[0] = value;
  } else if (key == "playerChoices2") {
    playerChoices[1] = value;
  } else if (key == "playerChoices3") {
    playerChoices[2] = value;
  } else {
    return false;
  }

  return true;
}

/**
 * @brief Loads the configuration from an INI-style string.
 * 
 * @param iniConfig The INI-style string containing the configuration.
 * @param gameMode The game mode to be set.
 * @param playerChoices Array of player choices to be set.
 * @return True if the configuration was successfully loaded, false otherwise.
 */
bool loadConfig(const String &iniConfig, int &gameMode, String playerChoices[]) {
  String line;
  bool success = true;

  for (int start = 0, end; start < iniConfig.length(); start = end + 1) {
    end = iniConfig.indexOf('\n', start);
    if (end == -1) end = iniConfig.length();

    line = iniConfig.substring(start, end);
    line.trim();

    if (!parseConfigLine(line, gameMode, playerChoices)) {
      success = false;
    }
  }

  return success;
}

/**
 * @brief Generates a random choice for the AI.
 * 
 * @return A string representing the AI's choice: Rock, Paper, or Scissors.
 */
String generateAIChoice() {
  int randomIndex = random(0, 3);
  return playerChoices[randomIndex];
}

/**
 * @brief Determines the winner between two players.
 * 
 * @param player1 The first player's choice.
 * @param player2 The second player's choice.
 * @return A string indicating the result of the match: "Draw", "Player 1 wins!", or "Player 2 wins!".
 */
String determineWinner(String player1, String player2) {
  int indexRock = 0;
  int indexPaper = 1;
  int indexScissors = 2;

  if (player1 == player2) return "Draw";

  if ((player1 == playerChoices[indexRock] && player2 == playerChoices[indexScissors]) ||
      (player1 == playerChoices[indexPaper] && player2 == playerChoices[indexRock]) ||
      (player1 == playerChoices[indexScissors] && player2 == playerChoices[indexPaper])) {
    return "Player 1 wins!";
  }

  return "Player 2 wins!";
}

/**
 * @brief Validates if a given move is a valid choice (Rock, Paper, or Scissors).
 * 
 * @param move The move to validate.
 * @return True if the move is valid, false otherwise.
 */
bool isValidMove(String move) {
  for (int i = 0; i < 3; i++) {
    if (move == playerChoices[i]) {
      return true;
    }
  }
  return false;
}

/**
 * @brief Initializes the game state, starting a new game.
 */
void initializeGame() {
  gameActive = true;
  Serial.println("Game started!");
}

/**
 * @brief Processes a Human vs AI game move.
 * 
 * @param humanChoice The human player's choice.
 */
void processHumanVsAI(String humanChoice) {
  if (!isValidMove(humanChoice)) {
    Serial.println("Invalid move. Valid moves are: Rock, Paper, Scissors.");
    return;
  }

  String aiChoice = generateAIChoice();
  Serial.println("AI chose: " + aiChoice);

  String result = determineWinner(humanChoice, aiChoice);
  Serial.println(result);
  gameActive = false;
}

/**
 * @brief Processes an AI vs AI game move.
 */
void processAIvsAI() {
  String ai1Choice = generateAIChoice();
  String ai2Choice = generateAIChoice();

  Serial.println("AI 1 chose: " + ai1Choice);
  Serial.println("AI 2 chose: " + ai2Choice);

  String result = determineWinner(ai1Choice, ai2Choice);
  Serial.println(result);
  gameActive = false;
}

/**
 * @brief Processes the received move based on the current game mode.
 * 
 * @param receivedMessage The received move or command.
 */
void processMove(String receivedMessage) {
  if (gameMode == 0) {
    processHumanVsAI(receivedMessage);
  } else if (gameMode == 2) {
    processAIvsAI();
  }
}

/**
 * @brief Handles the game mode based on the received message.
 * 
 * @param receivedMessage The received message indicating the desired game mode.
 */
void handleGameMode(String receivedMessage) {
  if (receivedMessage == "modes 0") {
    gameMode = 0;
    Serial.println("Game mode: Human vs AI");
  } else if (receivedMessage == "modes 1") {
    gameMode = 1;
    Serial.println("Game mode: Human vs Human");
  } else if (receivedMessage == "modes 2") {
    gameMode = 2;
    Serial.println("Game mode: AI vs AI");
  }

  GameConfig config = {gameMode, {playerChoices[0], playerChoices[1], playerChoices[2]}};
  saveConfig(config);
}

/**
 * @brief Processes the received message and performs the corresponding action.
 * 
 * @param receivedMessage The received message to process.
 */
void processReceivedMessage(String receivedMessage) {
  if (receivedMessage == "new") {
    initializeGame();
    if (gameMode == 2) {
      processAIvsAI();
    } else {
      Serial.println("Make your move (Rock, Paper, Scissors):");
    }
  } else if (receivedMessage.startsWith("modes")) {
    handleGameMode(receivedMessage);
  } else if (receivedMessage.startsWith("save")) {
    saveConfig(receivedMessage);
  } else if (receivedMessage.startsWith("game")) {
    loadConfig(receivedMessage, gameMode, playerChoices);
  } else if (gameActive) {
    processMove(receivedMessage);
  } else {
    Serial.println("No active game. Type 'new' to start.");
  }
}

/**
 * @brief Setup function to initialize the game.
 * 
 * Initializes the serial communication and random seed.
 */
void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(0));
}

/**
 * @brief Main loop to read and process received messages.
 */
void loop() {
  if (Serial.available() > 0) {
    String receivedMessage = Serial.readStringUntil('\n');
    receivedMessage.trim();
    processReceivedMessage(receivedMessage);
  }
}
