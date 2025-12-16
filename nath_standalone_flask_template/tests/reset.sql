-- Delete from mci_member table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mci_member') THEN
        DELETE FROM mci_member;
    END IF;
END $$;

-- Reset the sequence if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name = 'mci_member_mbr_id_seq') THEN
        ALTER SEQUENCE mci_member_mbr_id_seq RESTART WITH 1000;
    END IF;
END $$;
