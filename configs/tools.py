import requests

def send_sol(to_address: str, amount: float) -> str:
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