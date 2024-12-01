import requests

def solana_send_solana(to_address: str, amount: float) -> str:
        if to_address is None or amount is None:
            raise ValueError("Both to_address and amount must be provided")
        
        try:
            float_amount = float(amount)
        except ValueError:
            raise ValueError(f"Invalid amount: {amount}")

        transaction_function_template = """
            async (Connection,connection,SystemProgram,Transaction,sendAndConfirmTransaction,LAMPORTS_PER_SOL,PublicKey,StakeProgram,Keypair,VersionedTransaction,Buffer,fromKeypair,chainConfig) => {
 
            const transferInstruction = SystemProgram.transfer({fromPubkey: fromKeypair.publicKey,
            toPubkey: "RECIPIENT_ADDRESS",
            lamports: AMOUNT * LAMPORTS_PER_SOL,
            });

            const transaction = new Transaction().add(transferInstruction);

            const { blockhash } = await connection.getLatestBlockhash("confirmed");
            transaction.recentBlockhash = blockhash;
            transaction.feePayer = fromKeypair.publicKey;
            transaction.sign(fromKeypair);

            const signature = await connection.sendRawTransaction(transaction.serialize(), {
            skipPreflight: false,
            preflightCommitment: "confirmed",
            });
            let result = { transactionHash: signature  }
            return result.transactionHash;
            }
            """

     
        # Keep the original transaction_function_template
        temporary_template = transaction_function_template

        # Create a copy and modify it
        modified_template = temporary_template.replace("RECIPIENT_ADDRESS", to_address).replace("AMOUNT", str(float_amount))

        # Prepare the response as a JSON object
        modified_code_json = {
            "modifiedCode": modified_template
        }
        
        print(f"Generated modified code: {modified_code_json}")
        return modified_code_json

def solana_send_token(to_address: str, amount: float, token_mint: str) -> str:
    if to_address is None or amount is None or token_mint is None:
            raise ValueError("to_address, amount, and token_mint must be provided")
        
    try:
        float_amount = float(amount)
    except ValueError:
        raise ValueError(f"Invalid amount: {amount}")

    transaction_function_template = """
        
        async (Connection,connection,SystemProgram,Transaction,sendAndConfirmTransaction,LAMPORTS_PER_SOL,PublicKey,StakeProgram,Keypair,VersionedTransaction,Buffer,fromKeypair,chainConfig,web3_spl) =>{

            const receiverPubKey = new PublicKey('RECIPIENT_ADDRESS');  // replace with the receiver's address
            const mintPubKey = new PublicKey('TOKEN_ADDRESS');  // replace with token mint address

            const senderTokenAccount = await web3_spl.getOrCreateAssociatedTokenAccount(connection,fromKeypair,mintPubKey,fromKeypair.publicKey);
            const receiverTokenAccount = await web3_spl.getOrCreateAssociatedTokenAccount(connection,fromKeypair,mintPubKey,receiverPubKey);

            const senderTokenAccountInfo = await web3_spl.getAccount(connection, senderTokenAccount.address);
            const senderTokenBalance = senderTokenAccountInfo.amount;

            const mintInfo = await web3_spl.getMint(connection, mintPubKey);
            const mintDecimals = mintInfo.decimals;

            const transferAmount = BigInt( AMOUNT * 10**mintDecimals); // Amount to transfer in token's smallest unit

            if (senderTokenBalance < transferAmount) {
                console.log("Insufficient token balance for the transfer.");
                return;
            }

            const transferInstruction = web3_spl.createTransferCheckedInstruction(
                senderTokenAccount.address,
                mintPubKey,
                receiverTokenAccount.address,
                fromKeypair.publicKey,
                transferAmount, 
                mintDecimals 
            );

            const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash('finalized');

            const transaction = new Transaction({
                recentBlockhash: blockhash,
                feePayer: fromKeypair.publicKey,
            }).add(transferInstruction);
            
            transaction.sign(fromKeypair);
            const serializedTransaction = transaction.serialize();

            const transactionSignature = await connection.sendRawTransaction(
                serializedTransaction,
                { maxRetries: 5 }
            );

            let result = { transactionHash: transactionSignature };

            console.log("After result:",transactionSignature);

            return result.transactionHash;
        }
        """

    temporary_template = transaction_function_template
    modified_template = temporary_template.replace("RECIPIENT_ADDRESS", to_address).replace("AMOUNT", str(float_amount)).replace("TOKEN_ADDRESS", token_mint)

    modified_code_json = {
            "modifiedCode": modified_template
        }

    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json

def solana_create_and_delegate_stake(from_address: str, amount: float, validator_identifier: str) -> str:
        # logger.debug(f"Checking validator identifier: {validator_identifier}")
        vote_account = validator_identifier
        transaction_function_template = """
                async (Connection,connection,SystemProgram,Transaction,sendAndConfirmTransaction,LAMPORTS_PER_SOL,PublicKey,StakeProgram,Keypair,VersionedTransaction,Buffer,fromKeypair,chainConfig) => {
                    
                const stakeAccount = Keypair.generate();
                const rentExemptionAmount = await connection.getMinimumBalanceForRentExemption(StakeProgram.space);

                console.log("error here", rentExemptionAmount);

                const amountToStake = ( AMOUNT  * LAMPORTS_PER_SOL) + rentExemptionAmount;
                console.log("here 2");

                const createAccountTransaction = StakeProgram.createAccount({
                    fromPubkey: fromKeypair.publicKey,
                    stakePubkey: stakeAccount.publicKey,
                    authorized: {
                    staker: fromKeypair.publicKey,
                    withdrawer: fromKeypair.publicKey,
                    },
                    lamports: amountToStake,
                });

                console.log("here 3");

                const transaction = new Transaction();
                transaction.add(createAccountTransaction);

                const { blockhash } = await connection.getLatestBlockhash();
                transaction.recentBlockhash = blockhash;
                transaction.feePayer = fromKeypair.publicKey;

                transaction.sign(fromKeypair, stakeAccount);

                console.log("Sending create account transaction...");

                const rawTransaction = transaction.serialize();
                const signature = await connection.sendRawTransaction(rawTransaction, {
                    skipPreflight: false,
                    preflightCommitment: "confirmed",
                });
                console.log("Create account transaction sent with signature:", signature);

                let status = null;
                while (status === null || status.confirmationStatus !== 'confirmed') {
                    const response = await connection.getSignatureStatus(signature);
                    status = response.value;
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }

                console.log("Transaction confirmed");

                await new Promise(resolve => setTimeout(resolve, 5000));

                const delegateTransaction = StakeProgram.delegate({
                    stakePubkey: stakeAccount.publicKey,
                    authorizedPubkey: fromKeypair.publicKey,
                    votePubkey: new PublicKey( "VALIDATOR_VOTE_ACCOUNT" ),
                });
                console.log("here 5");

                console.log("delegatetxn here:", delegateTransaction);

                const delegateTx = new Transaction();
                delegateTx.add(delegateTransaction);

                const { blockhash: delegateBlockhash } = await connection.getLatestBlockhash();
                delegateTx.recentBlockhash = delegateBlockhash;
                delegateTx.feePayer = fromKeypair.publicKey;

                delegateTx.sign(fromKeypair);

                console.log("Sending delegate transaction...");

                const rawDelegateTransaction = delegateTx.serialize();
                const delegateSignature = await connection.sendRawTransaction(rawDelegateTransaction, {
                    skipPreflight: false,
                    preflightCommitment: "confirmed",
                });

                status = null;
                while (status === null || status.confirmationStatus !== 'confirmed') {
                    const response = await connection.getSignatureStatus(delegateSignature);
                    status = response.value;
                    await new Promise(resolve => setTimeout(resolve, 1000)); 
                }

                console.log("Delegate transaction sent with signature:", delegateSignature);

                let result = { transactionHash: delegateSignature };

                console.log("After result:", result, delegateSignature);

                return result.transactionHash;

                }

        """

        temporary_template = transaction_function_template
        modified_code = temporary_template.replace("VALIDATOR_VOTE_ACCOUNT", vote_account).replace("AMOUNT", str(amount))
        modified_code_json = {
            "modifiedCode": modified_code
        }
        
        print(f"Generated modified code: {modified_code_json}")
        return modified_code_json

def solana_create_stake_account(from_address: str, stake_account: str, amount: float) -> str:
    transaction_function_template = """
        async (connection, web3, fromKeypair, chainConfig, Buffer) => {
          const stakeAccount = new web3.Keypair();
          const minimumRent = await connection.getMinimumBalanceForRentExemption(web3.StakeProgram.space);
          const amountToStake = AMOUNT * web3.LAMPORTS_PER_SOL;

          const createAccountTransaction = web3.StakeProgram.createAccount({
            fromPubkey: fromKeypair.publicKey,
            stakePubkey: stakeAccount.publicKey,
            authorized: new web3.Authorized(fromKeypair.publicKey, fromKeypair.publicKey),
            lockup: new web3.Lockup(0, 0, fromKeypair.publicKey),
            lamports: minimumRent + amountToStake
          });

          const transaction = new web3.Transaction().add(createAccountTransaction);
          const { blockhash } = await connection.getLatestBlockhash("confirmed");
          transaction.recentBlockhash = blockhash;
          transaction.feePayer = fromKeypair.publicKey;
          transaction.sign(fromKeypair, stakeAccount);
          
          const signature = await connection.sendRawTransaction(transaction.serialize(), {
            skipPreflight: false,
            preflightCommitment: "confirmed",
          });
          
          let result = { transactionHash: signature, stakeAccountPublicKey: stakeAccount.publicKey.toBase58() }
          return JSON.stringify(result);
        }
        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("AMOUNT", str(float_amount))
    modified_code_json = {
            "modifiedCode": modified_code
        }
    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json

def solana_delegate_stake(stake_account: str, vote_account: str) -> str:
    transaction_function_template = """
        async (connection, web3, fromKeypair, chainConfig, Buffer) => {
          const delegateTransaction = web3.StakeProgram.delegate({
            stakePubkey: new web3.PublicKey('STAKE_ACCOUNT'),
            authorizedPubkey: fromKeypair.publicKey,
            votePubkey: new web3.PublicKey('VOTE_ACCOUNT')
          });

          const transaction = new web3.Transaction().add(delegateTransaction);
          const { blockhash } = await connection.getLatestBlockhash("confirmed");
          transaction.recentBlockhash = blockhash;
          transaction.feePayer = fromKeypair.publicKey;
          transaction.sign(fromKeypair);
          
          const signature = await connection.sendRawTransaction(transaction.serialize(), {
            skipPreflight: false,
            preflightCommitment: "confirmed",
          });
          
          let result = { transactionHash: signature }
          return result.transactionHash;
        }
        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account).replace("VOTE_ACCOUNT", vote_account)
    modified_code_json = {
            "modifiedCode": modified_code
        }
    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json

def solana_deactivate_stake(stake_account: str) -> str:
    transaction_function_template = """
        async (connection, web3, fromKeypair, chainConfig, Buffer) => {
          const deactivateTransaction = web3.StakeProgram.deactivate({
            stakePubkey: new web3.PublicKey('STAKE_ACCOUNT'),
            authorizedPubkey: fromKeypair.publicKey,
          });

          const transaction = new web3.Transaction().add(deactivateTransaction);
          const { blockhash } = await connection.getLatestBlockhash("confirmed");
          transaction.recentBlockhash = blockhash;
          transaction.feePayer = fromKeypair.publicKey;
          transaction.sign(fromKeypair);
          
          const signature = await connection.sendRawTransaction(transaction.serialize(), {
            skipPreflight: false,
            preflightCommitment: "confirmed",
          });
          
          let result = { transactionHash: signature }
          return result.transactionHash;
        }
        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account)
    modified_code_json = {
            "modifiedCode": modified_code
        }
    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json

def solana_withdraw_stake(stake_account: str, to_address: str, amount: float) -> str:
    transaction_function_template = """
        async (connection, web3, fromKeypair, chainConfig, Buffer) => {
          const withdrawTransaction = web3.StakeProgram.withdraw({
            stakePubkey: new web3.PublicKey('STAKE_ACCOUNT'),
            authorizedPubkey: fromKeypair.publicKey,
            toPubkey: new web3.PublicKey('TO_ADDRESS'),
            lamports: AMOUNT * web3.LAMPORTS_PER_SOL
          });

          const transaction = new web3.Transaction().add(withdrawTransaction);
          const { blockhash } = await connection.getLatestBlockhash("confirmed");
          transaction.recentBlockhash = blockhash;
          transaction.feePayer = fromKeypair.publicKey;
          transaction.sign(fromKeypair);
          
          const signature = await connection.sendRawTransaction(transaction.serialize(), {
            skipPreflight: false,
            preflightCommitment: "confirmed",
          });
          
          let result = { transactionHash: signature }
          return result.transactionHash;
        }
        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account).replace("TO_ADDRESS", to_address).replace("AMOUNT", str(float_amount))
    modified_code_json = {
            "modifiedCode": modified_code
    }
    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json

def solana_swap(input_token: str, output_token: str, amount: float, slippage: float, input_decimal: float) -> str:
    print(f"Input Token: {input_token} ({type(input_token)})")
    print(f"Output Token: {output_token} ({type(output_token)})")
    print(f"Amount: {amount} ({type(amount)})")
    print(f"Slippage: {slippage} ({type(slippage)})")
    print(f"Input Decimal: {input_decimal} ({type(input_decimal)})")
    transaction_function_template = """

    async (Connection,connection,SystemProgram,Transaction,sendAndConfirmTransaction,LAMPORTS_PER_SOL,PublicKey,StakeProgram,Keypair,VersionedTransaction,Buffer,fromKeypair,chainConfig) => {

        // const tokenInfo = {
        //   "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": { symbol: "USDC", decimals: 6 },
        //   "So11111111111111111111111111111111111111112": { symbol: "SOL", decimals: 9 },
        // };
      
      
        const inpToken = "INPUT_TOKEN" ;
        const outToken = "OUTPUT_TOKEN" ;
        // const amount =  AMOUNT * Math.pow(10, tokenInfo[inpToken].decimals);
        const amount =  AMOUNT * Math.pow(10, INPUT_DECIMAL);
        const slippage = SLIPPAGE * 100
      
        
      
        console.log("Wallet",fromKeypair);
      
        // Get the best route for a swap
        const quoteResponse = await (
          await fetch(
            `https://quote-api.jup.ag/v6/quote?inputMint=${inpToken}&outputMint=${outToken}&amount=${amount}&slippageBps=${slippage}`
          )
        ).json();
      
        console.log("QuickResposne: ",quoteResponse);
      
        const { swapTransaction } = await (
          await fetch("https://quote-api.jup.ag/v6/swap", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              quoteResponse,
              userPublicKey: fromKeypair.publicKey.toString(),
              wrapAndUnwrapSol: true,
            }),
          })
        ).json();
      
        console.log("swaptxn: ",swapTransaction);
      
        const swapTransactionBuf = Buffer.from(swapTransaction, "base64");
      
        const transaction = VersionedTransaction.deserialize(swapTransactionBuf);
        transaction.sign([fromKeypair]);
        console.log("Txn: ",transaction);
      
        const latestBlockHash = await connection.getLatestBlockhash();
        console.log("after blockhash: ",latestBlockHash)
        const simulationResult = await connection.simulateTransaction(transaction);
      console.log("Simulation result:", simulationResult);
      
      if (simulationResult.value.err) {
        throw new Error("Transaction simulation failed: " + JSON.stringify(simulationResult.value.err));
      }
      
        const rawTransaction = transaction.serialize();
        const txid = await connection.sendRawTransaction(rawTransaction, {
          skipPreflight: true,
          maxRetries: 2,
        });
        console.log("after rawtxn: ",rawTransaction,txid)
      
        let status = null;
        let cnt = 15;
        while ((status === null || status.confirmationStatus !== 'confirmed') && cnt>0) {
        const response = await connection.getSignatureStatus(txid);
        console.log("here ",response);
        status = response.value;
        await new Promise(resolve => setTimeout(resolve, 1000));
        cnt--;
        }
      
        if (status === null || status.confirmationStatus !== 'confirmed') {
          throw new Error("Transaction not confirmed after maximum retries");
        }
      
        let result = { transactionHash: txid };
      
        console.log("After result:", result);
      
        return result.transactionHash;
      }
        """
    float_amount = str(amount)
    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("INPUT_TOKEN", input_token).replace("OUTPUT_TOKEN", output_token).replace("AMOUNT", str(float_amount)).replace("SLIPPAGE",str(slippage)).replace("INPUT_DECIMAL",str(float(input_decimal)))
    modified_code_json = {
            "modifiedCode": modified_code
    }
    print(f"Generated modified code: {modified_code_json}")
    return modified_code_json