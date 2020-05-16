package keeper_test

import (
	"testing"

	"github.com/stretchr/testify/require"

	"github.com/bandprotocol/bandchain/chain/x/oracle/types"
)

func TestHasOracleScript(t *testing.T) {
	_, ctx, k := createTestInput()
	// We should not have a oracle script ID 42 without setting it.
	require.False(t, k.HasOracleScript(ctx, 42))
	// After we set it, we should be able to find it.
	k.SetOracleScript(ctx, 42, types.NewOracleScript(
		Owner.Address, BasicName, BasicDesc, BasicCode, BasicSchema, BasicSourceCodeURL,
	))
	require.True(t, k.HasOracleScript(ctx, 42))
}

func TestSetterGetterOracleScript(t *testing.T) {
	_, ctx, k := createTestInput()
	// Getting a non-existent oracle script should return error.
	_, err := k.GetOracleScript(ctx, 42)
	require.Error(t, err)
	require.Panics(t, func() { _ = k.MustGetOracleScript(ctx, 42) })
	// Creates some basic oracle scripts.
	oracleScript1 := types.NewOracleScript(
		Alice.Address, "NAME1", "DESCRIPTION1", []byte("code1"), BasicSchema, BasicSourceCodeURL,
	)
	oracleScript2 := types.NewOracleScript(
		Bob.Address, "NAME2", "DESCRIPTION2", []byte("code2"), BasicSchema, BasicSourceCodeURL,
	)
	// Sets id 42 with oracle script 1 and id 42 with oracle script 2.
	k.SetOracleScript(ctx, 42, oracleScript1)
	k.SetOracleScript(ctx, 43, oracleScript2)
	// Checks that Get and MustGet perform correctly.
	oracleScript1Res, err := k.GetOracleScript(ctx, 42)
	require.Nil(t, err)
	require.Equal(t, oracleScript1, oracleScript1Res)
	require.Equal(t, oracleScript1, k.MustGetOracleScript(ctx, 42))
	oracleScript2Res, err := k.GetOracleScript(ctx, 43)
	require.Nil(t, err)
	require.Equal(t, oracleScript2, oracleScript2Res)
	require.Equal(t, oracleScript2, k.MustGetOracleScript(ctx, 43))
	// Replaces id 42 with another oracle script.
	k.SetOracleScript(ctx, 42, oracleScript2)
	require.NotEqual(t, oracleScript1, k.MustGetOracleScript(ctx, 42))
	require.Equal(t, oracleScript2, k.MustGetOracleScript(ctx, 42))
}

func TestAddEditOracleScriptBasic(t *testing.T) {
	_, ctx, k := createTestInput()
	// Creates some basic oracle scripts.
	oracleScript1 := types.NewOracleScript(
		Alice.Address, "NAME1", "DESCRIPTION1", []byte("code1"), BasicSchema, BasicSourceCodeURL,
	)
	oracleScript2 := types.NewOracleScript(
		Bob.Address, "NAME2", "DESCRIPTION2", []byte("code2"), BasicSchema, BasicSourceCodeURL,
	)
	// Adds a new oracle script to the store. We should be able to retreive it back.
	id, err := k.AddOracleScript(ctx, types.NewOracleScript(
		oracleScript1.Owner, oracleScript1.Name, oracleScript1.Description, oracleScript1.Code,
		oracleScript1.Schema, oracleScript1.SourceCodeURL,
	))
	require.Nil(t, err)
	require.Equal(t, oracleScript1, k.MustGetOracleScript(ctx, id))
	require.NotEqual(t, oracleScript2, k.MustGetOracleScript(ctx, id))
	// Edits the oracle script. We should get the updated oracle script.
	err = k.EditOracleScript(ctx, id, types.NewOracleScript(
		oracleScript2.Owner, oracleScript2.Name, oracleScript2.Description, oracleScript2.Code,
		oracleScript2.Schema, oracleScript2.SourceCodeURL,
	))
	require.Nil(t, err)
	require.NotEqual(t, oracleScript1, k.MustGetOracleScript(ctx, id))
	require.Equal(t, oracleScript2, k.MustGetOracleScript(ctx, id))
}

func TestAddOracleScriptMustReturnCorrectID(t *testing.T) {
	_, ctx, k := createTestInput()
	// Initially we expect the oracle script count to be zero.
	count := k.GetOracleScriptCount(ctx)
	require.Equal(t, count, int64(0))
	// Every new oracle script we add should return a new ID.
	id1, err := k.AddOracleScript(ctx, types.NewOracleScript(
		Owner.Address, BasicName, BasicDesc, BasicCode, BasicSchema, BasicSourceCodeURL,
	))
	require.Nil(t, err)
	require.Equal(t, id1, types.OracleScriptID(1))
	// Adds another oracle script so now ID should be 2.
	id2, err := k.AddOracleScript(ctx, types.NewOracleScript(
		Owner.Address, BasicName, BasicDesc, BasicCode, BasicSchema, BasicSourceCodeURL,
	))
	require.Nil(t, err)
	require.Equal(t, id2, types.OracleScriptID(2))
	// Finally we expect the oracle script to increase to 2 since we added two oracle scripts.
	count = k.GetOracleScriptCount(ctx)
	require.Equal(t, count, int64(2))
}

func TestEditNonExistentOracleScript(t *testing.T) {
	_, ctx, k := createTestInput()
	// Editing a non-existent oracle script should return error.
	err := k.EditOracleScript(ctx, 42, types.NewOracleScript(
		Owner.Address, BasicName, BasicDesc, BasicCode, BasicSchema, BasicSourceCodeURL,
	))
	require.Error(t, err)
}

func TestGetAllOracleScripts(t *testing.T) {
	_, ctx, k := createTestInput()
	// Sets the oracle scripts to the storage.
	oracleScripts := []types.OracleScript{
		types.NewOracleScript(
			Alice.Address, "NAME1", "DESCRIPTION1", []byte("code1"),
			BasicSchema, BasicSourceCodeURL,
		),
		types.NewOracleScript(
			Bob.Address, "NAME2", "DESCRIPTION2", []byte("code2"),
			BasicSchema, BasicSourceCodeURL,
		),
	}
	k.SetOracleScript(ctx, 1, oracleScripts[0])
	k.SetOracleScript(ctx, 2, oracleScripts[1])
	// We should now be able to get all the existing oracle scripts.
	require.Equal(t, oracleScripts, k.GetAllOracleScripts(ctx))
}