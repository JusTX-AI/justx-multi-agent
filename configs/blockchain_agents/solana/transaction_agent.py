import requests
from configs.variables import SOLANA_SWAP_FEE_RATE, SOLANA_SWAP_FEE_SETELLMENT_ADDRESS

def solana_send_solana(to_address: str, amount: float) -> str:
        if to_address is None or amount is None:
            raise ValueError("Both to_address and amount must be provided")
        
        try:
            float_amount = float(amount)
        except ValueError:
            raise ValueError(f"Invalid amount: {amount}")

        transaction_function_template = """
            async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
                const transferInstruction = web3.SystemProgram.transfer({
                    fromPubkey: fromKeypair.publicKey,
                    toPubkey: new web3.PublicKey("RECIPIENT_ADDRESS"),
                    lamports: AMOUNT * web3.LAMPORTS_PER_SOL,
                });

                // Set compute unit limit and priority fee
                const computeUnitLimit = chainConfig.computeUnitLimit;
                const computeUnitPrice = chainConfig.computeUnitPrice;
                const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                });
                const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                });

                // Create transaction and add instructions
                const transaction = new web3.Transaction()
                    .add(transferInstruction)
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction);

                try {
                    // Send and confirm transaction using the built-in method
                    const signature = await web3.sendAndConfirmTransaction(
                        connection,
                        transaction,
                        [fromKeypair],
                        {
                            skipPreflight: false,
                            commitment: "confirmed",
                            maxRetries: 30
                        }
                    );
                    
                    return signature;
                } catch (error) {
                    console.log("Error in send sol",error);
                    throw new Error(`${error.message || error}`);
                }
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
        
        #print(f"Generated modified code: {modified_code_json}")
        print(modified_template)
        return modified_template

def solana_send_token(to_address: str, amount: float, token_mint: str) -> str:
    if to_address is None or amount is None or token_mint is None:
            raise ValueError("to_address, amount, and token_mint must be provided")
        
    try:
        float_amount = float(amount)
    except ValueError:
        raise ValueError(f"Invalid amount: {amount}")

    transaction_function_template = """
        async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
                try {
                    const receiverPubKey = new web3.PublicKey("RECIPIENT_ADDRESS");
                    const mintPubKey = new web3.PublicKey("TOKEN_ADDRESS");
            
                    // Utility to get or create associated token accounts manually
                    const getOrCreateAssociatedTokenAccountSafe = async (connection, payer, mint, owner, splToken) => {
                        const associatedTokenAddress = await splToken.getAssociatedTokenAddress(mint, owner);
                        try {
                            
                            await splToken.getAccount(connection, associatedTokenAddress);
                            return { address: associatedTokenAddress, newlyCreated: false };
                        } catch (e) {
                           
                            const transaction = new web3.Transaction().add(
                                splToken.createAssociatedTokenAccountInstruction(
                                    payer.publicKey, // Payer of the transaction
                                    associatedTokenAddress, // Address of the new token account
                                    owner, // Owner of the token account
                                    mint // Token mint
                                )
                            );
                            await web3.sendAndConfirmTransaction(connection, transaction, [payer]);
                            return { address: associatedTokenAddress, newlyCreated: true };
                        }
                    };
            
                    // Get or create token accounts
                    const senderTokenAccount = await web3_spl.getOrCreateAssociatedTokenAccount(
                        connection,
                        fromKeypair,
                        mintPubKey,
                        fromKeypair.publicKey
                    );
                    console.log("Sender token account: ", senderTokenAccount);
            
                    const receiverTokenAccount = await getOrCreateAssociatedTokenAccountSafe(
                        connection,
                        fromKeypair,
                        mintPubKey,
                        receiverPubKey,
                        web3_spl
                    );
                    console.log("Receiver token account: ", receiverTokenAccount);
            
                    // Get account and mint info
                    const [senderTokenAccountInfo, mintInfo] = await Promise.all([
                        web3_spl.getAccount(connection, senderTokenAccount.address),
                        web3_spl.getMint(connection, mintPubKey),
                    ]);
                    console.log("Sender token account info: ", senderTokenAccountInfo);
                    console.log("Mint info: ", mintInfo);
            
                    // Check balance
                    const transferAmount = BigInt(Math.floor( AMOUNT * 10 ** mintInfo.decimals));
                    if (senderTokenAccountInfo.amount < transferAmount) {
                        throw new Error("Insufficient token balance");
                    }
            
                    // Create transfer instruction
                    const transferInstruction = web3_spl.createTransferCheckedInstruction(
                        senderTokenAccount.address,
                        mintPubKey,
                        receiverTokenAccount.address,
                        fromKeypair.publicKey,
                        transferAmount,
                        mintInfo.decimals
                    );
            
                    // Add compute unit limit and priority fee instructions
                    const computeUnitLimit = chainConfig.computeUnitLimit;
                    const computeUnitPrice = chainConfig.computeUnitPrice;
                    const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                        units: computeUnitLimit,
                    });
                    const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                        microLamports: computeUnitPrice,
                    });
            
                    // Create and configure transaction
                    const transaction = new web3.Transaction()
                        .add(computeUnitInstruction)
                        .add(addPriorityFeeInstruction)
                        .add(transferInstruction);
            
                    // Send and confirm transaction
                    const signature = await web3.sendAndConfirmTransaction(
                        connection,
                        transaction,
                        [fromKeypair],
                        {
                            skipPreflight: false,
                            commitment: "confirmed",
                            maxRetries: 5
                        }
                    );
            
                    return signature;
                } catch (error) {
                    console.log("Token transfer failed:", error);
                    throw new Error(error.message || error);
                }
            }

        """

    temporary_template = transaction_function_template
    modified_template = temporary_template.replace("RECIPIENT_ADDRESS", to_address).replace("AMOUNT", str(float_amount)).replace("TOKEN_ADDRESS", token_mint)

    modified_code_json = {
            "modifiedCode": modified_template
        }

    #print(f"Generated modified code: {modified_code_json}")
    print(modified_template)
    return modified_template

def solana_create_and_delegate_stake(from_address: str, amount: float, validator_identifier: str) -> str:
        # logger.debug(f"Checking validator identifier: {validator_identifier}")
        vote_account = validator_identifier
        transaction_function_template = """
           async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
                try {
                  // Create new stake account keypair
                  const stakeAccount = web3.Keypair.generate();
                  
                  // Calculate required lamports
                  const minimumRent = await connection.getMinimumBalanceForRentExemption(web3.StakeProgram.space);
                  const amountToStake = AMOUNT * web3.LAMPORTS_PER_SOL;
                  const totalAmount = minimumRent + amountToStake;
              
                  // Create stake account instruction
                  const createAccountTransaction = web3.StakeProgram.createAccount({
                    fromPubkey: fromKeypair.publicKey,
                    stakePubkey: stakeAccount.publicKey,
                    authorized: new web3.Authorized(fromKeypair.publicKey, fromKeypair.publicKey),
                    lockup: new web3.Lockup(0, 0, fromKeypair.publicKey),
                    lamports: totalAmount
                  });
              
                  // Add compute unit limit and priority fee instructions
                  const computeUnitLimit = chainConfig.computeUnitLimit;
                  const computeUnitPrice = chainConfig.computeUnitPrice;
                  const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                  });
                  const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                  });
              
                  // Create and send stake account creation transaction
                  const createTransaction = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(createAccountTransaction);
              
                  console.log("Sending create account transaction...");
                  const createSignature = await web3.sendAndConfirmTransaction(
                    connection,
                    createTransaction,
                    [fromKeypair, stakeAccount],
                    {
                      skipPreflight: false,
                      commitment: "confirmed",
                      maxRetries: 30
                    }
                  );
                  console.log("Created stake account:", stakeAccount.publicKey.toString());
                  console.log("Create transaction signature:", createSignature);
              
                  // Wait for confirmation and add some delay
                  await new Promise(resolve => setTimeout(resolve, 5000));
              
                  // Create delegation transaction
                  const delegateTransaction = web3.StakeProgram.delegate({
                    stakePubkey: stakeAccount.publicKey,
                    authorizedPubkey: fromKeypair.publicKey,
                    votePubkey: new web3.PublicKey("VALIDATOR_VOTE_ACCOUNT"),
                  });
              
                  // Create and send delegation transaction
                  const delegateTx = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(delegateTransaction);
              
                  console.log("Sending delegate transaction...");
                  const delegateSignature = await web3.sendAndConfirmTransaction(
                    connection,
                    delegateTx,
                    [fromKeypair],
                    {
                      skipPreflight: false,
                      commitment: "confirmed",
                      maxRetries: 30
                    }
                  );
                  
                  console.log("Delegate transaction signature:", delegateSignature);
              
                  return delegateSignature;
              
                } catch (error) {
                  console.error("Staking operation failed:", error);
                  throw new Error("Staking failed:",error.message || error);
                }
              }

        """

        temporary_template = transaction_function_template
        modified_code = temporary_template.replace("VALIDATOR_VOTE_ACCOUNT", vote_account).replace("AMOUNT", str(amount))
        modified_code_json = {
            "modifiedCode": modified_code
        }
        
        #print(f"Generated modified code: {modified_code_json}")
        print(modified_code)
        return modified_code

def solana_create_stake_account(from_address: str, stake_account: str, amount: float) -> str:
    transaction_function_template = """
       async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
            try {
                // Create new stake account keypair
                const stakeAccount = new web3.Keypair();
                
                // Calculate required lamports
                const minimumRent = await connection.getMinimumBalanceForRentExemption(web3.StakeProgram.space);
                const amountToStake = AMOUNT * web3.LAMPORTS_PER_SOL;

                // Create stake account instruction
                const createAccountTransaction = web3.StakeProgram.createAccount({
                    fromPubkey: fromKeypair.publicKey,
                    stakePubkey: stakeAccount.publicKey,
                    authorized: new web3.Authorized(fromKeypair.publicKey, fromKeypair.publicKey),
                    lockup: new web3.Lockup(0, 0, fromKeypair.publicKey),
                    lamports: minimumRent + amountToStake
                });

                // Add compute unit limit and priority fee instructions
                const computeUnitLimit = chainConfig.computeUnitLimit;
                const computeUnitPrice = chainConfig.computeUnitPrice;
                const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                });
                const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                });

                // Create transaction and add all instructions
                const transaction = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(createAccountTransaction);

                // Send and confirm transaction
                const signature = await web3.sendAndConfirmTransaction(
                    connection,
                    transaction,
                    [fromKeypair, stakeAccount], // Note: both keypairs needed for signing
                    {
                        skipPreflight: false,
                        commitment: "confirmed",
                        maxRetries: 30
                    }
                );

                console.log("Created stake account:", stakeAccount.publicKey.toString());
                return signature;
            } catch (error) {
                        console.log("Create Stake Account failed:", error);
                        throw new Error(`${error.message || error}`);
                    }
        }

        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("AMOUNT", str(float_amount))
    modified_code_json = {
            "modifiedCode": modified_code
        }
    #print(f"Generated modified code: {modified_code_json}")
    print(modified_code)
    return modified_code

def solana_delegate_stake(stake_account: str, vote_account: str) -> str:
    transaction_function_template = """
        async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
            try {
                // Create delegation instruction
                const delegateTransaction = web3.StakeProgram.delegate({
                    stakePubkey: new web3.PublicKey("STAKE_ACCOUNT"),
                    authorizedPubkey: fromKeypair.publicKey,
                    votePubkey: new web3.PublicKey("VOTE_ACCOUNT"),
                });

                // Add compute unit limit and priority fee instructions
                const computeUnitLimit = chainConfig.computeUnitLimit;
                const computeUnitPrice = chainConfig.computeUnitPrice;
                const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                });
                const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                });

                // Create transaction and add all instructions
                const transaction = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(delegateTransaction);

                // Send and confirm transaction
                const signature = await web3.sendAndConfirmTransaction(
                    connection,
                    transaction,
                    [fromKeypair],
                    {
                        skipPreflight: false,
                        commitment: "confirmed",
                        maxRetries: 30
                    }
                );

                console.log("Successfully delegated stake account");
                return signature;
            } catch (error) {
                        console.log("Delegate Stake failed:", error);
                        throw new Error(`${error.message || error}`);
                    }
        }

        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account).replace("VOTE_ACCOUNT", vote_account)
    modified_code_json = {
            "modifiedCode": modified_code
        }
    #print(f"Generated modified code: {modified_code_json}")
    print(modified_code)
    return modified_code

def solana_deactivate_stake(stake_account: str) -> str:
    transaction_function_template = """
       async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
            try {
                // Create deactivation instruction
                const deactivateTransaction = web3.StakeProgram.deactivate({
                    stakePubkey: new web3.PublicKey('STAKE_ACCOUNT'),
                    authorizedPubkey: fromKeypair.publicKey,
                });

                // Add compute unit limit and priority fee instructions
                const computeUnitLimit = chainConfig.computeUnitLimit;
                const computeUnitPrice = chainConfig.computeUnitPrice;
                const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                });
                const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                });

                // Create transaction and add all instructions
                const transaction = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(deactivateTransaction);

                // Send and confirm transaction
                const signature = await web3.sendAndConfirmTransaction(
                    connection,
                    transaction,
                    [fromKeypair],
                    {
                        skipPreflight: false,
                        commitment: "confirmed",
                        maxRetries: 30
                    }
                );

                console.log("Successfully deactivated stake account");
                return signature;
            } catch (error) {
                        console.log("Deactivating Stake failed:", error);
                        throw new Error(`${error.message || error}`);
                    }
        }

        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account)
    modified_code_json = {
            "modifiedCode": modified_code
        }
    #print(f"Generated modified code: {modified_code_json}")
    print(modified_code)
    return modified_code

def solana_withdraw_stake(stake_account: str, to_address: str, amount: float) -> str:
    transaction_function_template = """
        async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {
            try {
                // Create withdrawal instruction
                const withdrawTransaction = web3.StakeProgram.withdraw({
                    stakePubkey: new web3.PublicKey('STAKE_ACCOUNT'),
                    authorizedPubkey: fromKeypair.publicKey,
                    toPubkey: new web3.PublicKey('TO_ADDRESS'),
                    lamports: STAKE_AMOUNT
                });

                // Add compute unit limit and priority fee instructions
                const computeUnitLimit = chainConfig.computeUnitLimit;
                const computeUnitPrice = chainConfig.computeUnitPrice;
                const computeUnitInstruction = web3.ComputeBudgetProgram.setComputeUnitLimit({
                    units: computeUnitLimit,
                });
                const addPriorityFeeInstruction = web3.ComputeBudgetProgram.setComputeUnitPrice({
                    microLamports: computeUnitPrice,
                });

                // Create transaction and add all instructions
                const transaction = new web3.Transaction()
                    .add(computeUnitInstruction)
                    .add(addPriorityFeeInstruction)
                    .add(withdrawTransaction);

                // Send and confirm transaction
                const signature = await web3.sendAndConfirmTransaction(
                    connection,
                    transaction,
                    [fromKeypair],
                    {
                        skipPreflight: false,
                        commitment: "confirmed",
                        maxRetries: 30
                    }
                );

                console.log("Successfully withdrew from stake account");
                return signature;
            } catch (error) {
                        console.log("Withdrawl of stake failed:", error);
                        throw new Error(`${error.message || error}`);
                    }
        }
        """

    temporary_template = transaction_function_template
    modified_code = temporary_template.replace("STAKE_ACCOUNT", stake_account).replace("TO_ADDRESS", to_address).replace("STAKE_AMOUNT", str(float_amount))
    modified_code_json = {
            "modifiedCode": modified_code
    }
    #print(f"Generated modified code: {modified_code_json}")
    print(modified_code)
    return modified_code

def solana_swap(input_token: str, output_token: str, amount: float, slippage: float, input_decimal: float) -> str:
    print(f"Input Token: {input_token} ({type(input_token)})")
    print(f"Output Token: {output_token} ({type(output_token)})")
    print(f"Amount: {amount} ({type(amount)})")
    print(f"Slippage: {slippage} ({type(slippage)})")
    print(f"Input Decimal: {input_decimal} ({type(input_decimal)})")
    
    function_code = f"""async (connection, web3, Buffer, fromKeypair, chainConfig, web3_spl) => {{
    try {{
        const inputToken = "{input_token}";
        const outputToken = "{output_token}";
        const inputAmount = Math.floor({amount} * Math.pow(10, {input_decimal}));
        const slippage = {slippage} * 100;

        const swapFeeRate = {SOLANA_SWAP_FEE_RATE}; // {SOLANA_SWAP_FEE_RATE*100}%
        const swapFeeSettlementAccountAddress = "{SOLANA_SWAP_FEE_SETELLMENT_ADDRESS}";

        const swapFeeAmount = Math.floor(inputAmount * swapFeeRate);
        const swapAmount = inputAmount - swapFeeAmount;

        const quoteURL = `https://quote-api.jup.ag/v6/quote?inputMint=${{inputToken}}&outputMint=${{outputToken}}&amount=${{swapAmount}}&slippageBps=${{slippage}}`;
        const quoteResponse = await (await fetch(quoteURL)).json();
        if (quoteResponse.error) {{
        throw new Error("Error getting quote");
        }}

        if (!quoteResponse) {{
        throw new Error("Error getting quote for swap");
        }}

        const {{ swapTransaction }} = await (
        await fetch("https://quote-api.jup.ag/v6/swap", {{
            method: "POST",
            headers: {{
            "Content-Type": "application/json",
            }},
            body: JSON.stringify({{
            quoteResponse,
            userPublicKey: fromKeypair.publicKey.toString(),
            wrapAndUnwrapSol: true,
            dynamicComputeUnitLimit: true,
            prioritizationFeeLamports: parseInt(chainConfig.feeAmount) || "auto",
            }}),
        }})
        ).json();

        const swapTransactionBuf = Buffer.from(swapTransaction, "base64");
        var transaction = web3.VersionedTransaction.deserialize(swapTransactionBuf);

        let transferInstruction = null;
        if (inputToken === web3_spl.NATIVE_MINT.toString()) {{
        transferInstruction = web3.SystemProgram.transfer({{
            fromPubkey: fromKeypair.publicKey,
            toPubkey: new web3.PublicKey(swapFeeSettlementAccountAddress),
            lamports: swapFeeAmount,
        }});
        }} else {{
        const tokenMintPubkey = new web3.PublicKey(inputToken);

        // Get or create the recipient's associated token account
        const recipientTokenAccount =
            await web3_spl.getOrCreateAssociatedTokenAccount(
            connection,
            fromKeypair,
            tokenMintPubkey,
            new web3.PublicKey(swapFeeSettlementAccountAddress)
            );

        const senderTokenAccount =
            await web3_spl.getOrCreateAssociatedTokenAccount(
            connection,
            fromKeypair,
            tokenMintPubkey,
            fromKeypair.publicKey
            );

        transferInstruction = web3_spl.createTransferInstruction(
            senderTokenAccount.address,
            recipientTokenAccount.address,
            fromKeypair.publicKey,
            swapFeeAmount,
            [],
            web3_spl.TOKEN_PROGRAM_ID
        );
        }}

        const addressLookupTableAccounts = await Promise.all(
        transaction.message.addressTableLookups.map(async (lookup) => {{
            return new web3.AddressLookupTableAccount({{
            key: lookup.accountKey,
            state: web3.AddressLookupTableAccount.deserialize(
                await connection
                .getAccountInfo(lookup.accountKey)
                .then((res) => res.data)
            ),
            }});
        }})
        );

        var message = web3.TransactionMessage.decompile(transaction.message, {{
        addressLookupTableAccounts: addressLookupTableAccounts,
        }});
        message.instructions.push(transferInstruction);

        transaction.message = message.compileToV0Message(
        addressLookupTableAccounts
        );

        const {{ blockhash, lastValidBlockHeight }} =
        await connection.getLatestBlockhash("confirmed");

        // @ts-ignore
        transaction.recentBlockhash = blockhash;
        // @ts-ignore
        transaction.feePayer = fromKeypair.publicKey;

        // Sign the transaction
        transaction.sign([fromKeypair]);

        const signature = await connection.sendRawTransaction(
        transaction.serialize(),
        {{
            skipPreflight: false,
            maxRetries: 5,
        }}
        );

        // Polling confirmation
        let confirmed = false;
        let retries = 30;
        while (!confirmed && retries > 0) {{
        const status = await connection.getSignatureStatus(signature);
        console.log(retries, status);
        if (status?.value?.confirmationStatus === "confirmed") {{
            confirmed = true;
            break;
        }}
        await new Promise((resolve) => setTimeout(resolve, 1000));
        retries--;
        }}

        if (!confirmed) {{
        throw new Error("Transaction confirmation timeout");
        }}

        console.log("Tx signature", signature);
        return signature;
    }} catch (error) {{
        console.log("Jupiter swap failed:", error);
        throw error;
    }}
}}"""
    return function_code