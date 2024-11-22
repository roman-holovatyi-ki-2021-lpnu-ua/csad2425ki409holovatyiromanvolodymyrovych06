#include <Arduino.h>

bool gameActive = false;
String playerChoices[3] = {"Rock", "Paper", "Scissors"};
int gameMode = 0;

struct GameConfig {
  int gameMode;
  String playerChoices[3];
};

String saveConfig(const GameConfig &config) {
  String iniConfig;
  
  iniConfig += "gameMode=" + String(config.gameMode) + "\n";
  iniConfig += "playerChoices1=" + config.playerChoices[0] + "\n";
  iniConfig += "playerChoices2=" + config.playerChoices[1] + "\n";
  iniConfig += "playerChoices3=" + config.playerChoices[2] + "\n";
  
  return iniConfig;
}

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



String generateAIChoice() {
  int randomIndex = random(0, 3);
  return playerChoices[randomIndex];
}

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

bool isValidMove(String move) {
  for (int i = 0; i < 3; i++) {
    if (move == playerChoices[i]) {
      return true;
    }
  }
  return false;
}

void initializeGame() {
  gameActive = true;
  Serial.println("Game started!");
}

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

void processAIvsAI() {
  String ai1Choice = generateAIChoice();
  String ai2Choice = generateAIChoice();

  Serial.println("AI 1 chose: " + ai1Choice);
  Serial.println("AI 2 chose: " + ai2Choice);

  String result = determineWinner(ai1Choice, ai2Choice);
  Serial.println(result);
  gameActive = false;
}

void processMove(String receivedMessage) {
  if (gameMode == 0) {
    processHumanVsAI(receivedMessage);
  } else if (gameMode == 2) {
    processAIvsAI();
  }
}

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
  } else if (receivedMessage.startsWith("game")) {
    loadConfig(receivedMessage, gameMode, playerChoices);
  } else if (gameActive) {
    processMove(receivedMessage);
  } else {
    Serial.println("No active game. Type 'new' to start.");
  }
}

void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(0));
}

void loop() {
  if (Serial.available() > 0) {
    String receivedMessage = Serial.readStringUntil('\n');
    receivedMessage.trim();
    processReceivedMessage(receivedMessage);
  }
}
