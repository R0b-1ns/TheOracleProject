// ---------------------------------------------------------------------------
// Interaction avec le contrat via Taquito
// ---------------------------------------------------------------------------

import { TezosToolkit } from "@taquito/taquito";
import type { Prediction, OracleProfile, LeaderboardEntry } from "../types";
import { STATUS_MAP, getOracleRank, winRate } from "../types";

// Adresse du contrat déployé sur Ghostnet
export const CONTRACT_ADDRESS =
  import.meta.env.VITE_CONTRACT_ADDRESS ?? "KT1PLACEHOLDER_GHOSTNET";

// RPC Ghostnet
export const GHOSTNET_RPC = "https://rpc.ghostnet.teztnets.com";

export const Tezos = new TezosToolkit(GHOSTNET_RPC);

// ---------------------------------------------------------------------------
// Lecture du storage via Taquito
// ---------------------------------------------------------------------------

export async function fetchPredictions(): Promise<Prediction[]> {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  const storage  = await contract.storage<any>();

  const predictions: Prediction[] = [];
  const count: number = storage.prediction_count.toNumber();

  for (let i = 0; i < count; i++) {
    const raw = await storage.predictions.get(i);
    if (!raw) continue;

    const bets: any[] = [];
    const betCount = raw.bet_count.toNumber();
    for (let j = 0; j < betCount; j++) {
      const b = await raw.bets.get(j);
      if (b) {
        bets.push({
          bettor:     b.bettor,
          choice:     b.choice.toNumber(),
          amount:     b.amount.toNumber(),
          confidence: b.confidence.toNumber(),
          claimed:    b.claimed,
        });
      }
    }

    predictions.push({
      id:            i,
      creator:       raw.creator,
      description:   raw.description,
      deadline:      new Date(raw.deadline * 1000).toISOString(),
      options:       raw.options,
      status:        STATUS_MAP[raw.status.toNumber()] ?? "open",
      winningOption: raw.winning_option ? raw.winning_option.toNumber() : null,
      totalPool:     raw.total_pool.toNumber(),
      bets,
    });
  }

  return predictions;
}

export async function fetchElo(address: string): Promise<number> {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  const storage  = await contract.storage<any>();
  const elo = await storage.elo_scores.get(address);
  return elo ? elo.toNumber() : 1000;
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  const storage  = await contract.storage<any>();

  // Récupère tous les scores ELO depuis le big_map
  const eloMap = storage.elo_scores;
  const entries: LeaderboardEntry[] = [];

  // Itération sur les clés du big_map via l'indexer Ghostnet
  const resp = await fetch(
    `https://api.ghostnet.tzkt.io/v1/contracts/${CONTRACT_ADDRESS}/bigmaps/elo_scores/keys?limit=100`
  );
  const keys = await resp.json();

  for (const key of keys) {
    const addr = key.key;
    const elo  = parseInt(key.value, 10);
    entries.push({
      rank:        0,
      address:     addr,
      elo,
      oracleRank:  getOracleRank(elo),
      wins:        0,
      predictions: 0,
      winRate:     0,
    });
  }

  // Trier par ELO décroissant et attribuer les rangs
  entries.sort((a, b) => b.elo - a.elo);
  entries.forEach((e, i) => { e.rank = i + 1; });

  return entries;
}

// ---------------------------------------------------------------------------
// Écriture sur la blockchain
// ---------------------------------------------------------------------------

export async function txCreatePrediction(
  description: string,
  deadlineIso: string,
  options: string[]
) {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  const deadline = Math.floor(new Date(deadlineIso).getTime() / 1000);
  return contract.methods
    .create_prediction(description, deadline, options)
    .send();
}

export async function txPlaceBet(
  predictionId: number,
  choice: number,
  confidence: number,
  amountTez: number
) {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  return contract.methods
    .place_bet(predictionId, choice, confidence)
    .send({ amount: amountTez });
}

export async function txClaimReward(predictionId: number, betIndex: number) {
  const contract = await Tezos.contract.at(CONTRACT_ADDRESS);
  return contract.methods
    .claim_reward(predictionId, betIndex)
    .send();
}
