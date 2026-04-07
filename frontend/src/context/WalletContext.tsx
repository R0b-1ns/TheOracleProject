// ---------------------------------------------------------------------------
// WalletContext — Connexion Beacon / Temple Wallet
// ---------------------------------------------------------------------------

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { BeaconWallet } from "@taquito/beacon-wallet";
import { NetworkType } from "@airgap/beacon-sdk";
import { Tezos } from "../utils/contract";
import { fetchElo } from "../utils/contract";
import { getOracleRank } from "../types";
import type { OracleRank } from "../types";

interface WalletState {
  address:    string | null;
  elo:        number;
  rank:       OracleRank;
  connecting: boolean;
  connect:    () => Promise<void>;
  disconnect: () => Promise<void>;
}

const WalletContext = createContext<WalletState | null>(null);

let walletInstance: BeaconWallet | null = null;

function getWallet(): BeaconWallet {
  if (!walletInstance) {
    walletInstance = new BeaconWallet({
      name:        "The Oracle Protocol",
      preferredNetwork: NetworkType.GHOSTNET,
    });
  }
  return walletInstance;
}

export function WalletProvider({ children }: { children: ReactNode }) {
  const [address,    setAddress]    = useState<string | null>(null);
  const [elo,        setElo]        = useState<number>(1000);
  const [connecting, setConnecting] = useState(false);

  const rank: OracleRank = getOracleRank(elo);

  // Restore session on mount
  useEffect(() => {
    const wallet = getWallet();
    Tezos.setWalletProvider(wallet);

    wallet.client.getActiveAccount().then(async (account) => {
      if (account) {
        setAddress(account.address);
        try {
          const score = await fetchElo(account.address);
          setElo(score);
        } catch {
          // contrat pas encore déployé en dev
        }
      }
    });
  }, []);

  const connect = useCallback(async () => {
    setConnecting(true);
    try {
      const wallet = getWallet();
      await wallet.requestPermissions({
        network: { type: NetworkType.GHOSTNET },
      });
      const addr = await wallet.getPKH();
      setAddress(addr);
      const score = await fetchElo(addr).catch(() => 1000);
      setElo(score);
    } finally {
      setConnecting(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    const wallet = getWallet();
    await wallet.clearActiveAccount();
    setAddress(null);
    setElo(1000);
  }, []);

  return (
    <WalletContext.Provider value={{ address, elo, rank, connecting, connect, disconnect }}>
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet(): WalletState {
  const ctx = useContext(WalletContext);
  if (!ctx) throw new Error("useWallet must be used inside WalletProvider");
  return ctx;
}
