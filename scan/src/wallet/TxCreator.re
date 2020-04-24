type msg_send_t = {
  to_address: string,
  from_address: string,
  amount: array(Coin.t),
};

type msg_request_t = {
  oracleScriptID: string,
  calldata: string,
  requestedValidatorCount: string,
  sufficientValidatorCount: string,
  sender: string,
  clientID: string,
};

type amount_t = {
  amount: string,
  denom: string,
};

type fee_t = {
  amount: array(amount_t),
  gas: string,
};

type msg_input_t =
  | Send(Address.t, Address.t, Coin.t)
  | Request(ID.OracleScript.t, JsBuffer.t, string, string, Address.t, string);

type msg_payload_t = {
  [@bs.as "type"]
  type_: string,
  value: Js.Json.t,
};

type account_result_t = {
  accountNumber: int,
  sequence: int,
};

type pub_key_t = {
  [@bs.as "type"]
  type_: string,
  value: string,
};

type signature_t = {
  pub_key: pub_key_t,
  public_key: string,
  signature: string,
};

type raw_tx_t = {
  msgs: array(msg_payload_t),
  chain_id: string,
  fee: fee_t,
  memo: string,
  account_number: string,
  sequence: string,
};

type signed_tx_t = {
  fee: fee_t,
  memo: string,
  msgs: array(msg_payload_t),
  signatures: array(signature_t),
};

type t = {
  mode: string,
  tx: signed_tx_t,
};

let getAccountInfo = address => {
  let%Promise info = AxiosRequest.accountInfo(address);
  let data = info##data;
  Promise.ret(
    JsonUtils.Decode.{
      accountNumber: data |> at(["result", "value", "account_number"], int),
      sequence: data |> at(["result", "value", "sequence"], int),
    },
  );
};

let createMsg = (msg: msg_input_t): msg_payload_t => {
  let msgType =
    switch (msg) {
    | Send(_) => "cosmos-sdk/MsgSend"
    | Request(_) => "oracle/Request"
    };

  let msgValue =
    switch (msg) {
    | Send(fromAddress, toAddress, coins) =>
      Js.Json.stringifyAny({
        to_address: toAddress |> Address.toBech32,
        from_address: fromAddress |> Address.toBech32,
        amount: [|coins|],
      })
      |> Belt_Option.getExn
      |> Js.Json.parseExn
    | Request(
        ID.OracleScript.ID(oracleScriptID),
        calldata,
        requestedValidatorCount,
        sufficientValidatorCount,
        sender,
        clientID,
      ) =>
      Js.Json.stringifyAny({
        oracleScriptID: oracleScriptID |> string_of_int,
        calldata: calldata |> JsBuffer.toBase64,
        requestedValidatorCount,
        sufficientValidatorCount,
        sender: sender |> Address.toBech32,
        clientID,
      })
      |> Belt_Option.getExn
      |> Js.Json.parseExn
    };
  {type_: msgType, value: msgValue};
};

// TODO: Reme hardcoded values
let createRawTx = (address, msgs) => {
  let%Promise accountInfo = getAccountInfo(address);
  Promise.ret({
    msgs: msgs->Belt_Array.map(createMsg),
    chain_id: "bandchain",
    fee: {
      amount: [|{amount: "100", denom: "uband"}|],
      gas: "300000",
    },
    memo: "",
    account_number: accountInfo.accountNumber |> string_of_int,
    sequence: accountInfo.sequence |> string_of_int,
  });
};

let createSignedTx = (~signature, ~pubKey, ~tx: raw_tx_t, ~mode, ()) => {
  let oldPubKey = {type_: "tendermint/PubKeySecp256k1", value: pubKey |> PubKey.toBase64};
  let newPubKey = "eb5ae98721" ++ (pubKey |> PubKey.toHex) |> JsBuffer.hexToBase64;
  let signedTx = {
    fee: tx.fee,
    memo: tx.memo,
    msgs: tx.msgs,
    signatures: [|{pub_key: oldPubKey, public_key: newPubKey, signature}|],
  };
  {mode, tx: signedTx};
};