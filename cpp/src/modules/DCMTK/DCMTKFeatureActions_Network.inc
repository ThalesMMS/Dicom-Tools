void DCMTKTests::TestNetworkEchoAndStore(const std::string& filename, const std::string& outputDir) {
    // Spin up a tiny in-process SCP and exercise C-ECHO + C-STORE locally
    std::cout << "--- [DCMTK] C-ECHO / C-STORE Loopback ---" << std::endl;
#ifdef USE_DCMTK
    DcmFileFormat input;
    OFCondition loadStatus = input.loadFile(filename.c_str());
    if (loadStatus.bad()) {
        std::cerr << "Unable to load input for network test: " << loadStatus.text() << std::endl;
        return;
    }

    DcmDataset* inputDataset = input.getDataset();
    OFString sopClass;
    OFString sopInstance;
    if (inputDataset->findAndGetOFString(DCM_SOPClassUID, sopClass).bad() || sopClass.empty()) {
        sopClass = UID_CTImageStorage;
    }
    inputDataset->findAndGetOFString(DCM_SOPInstanceUID, sopInstance);

    OFList<OFString> syntaxes = DefaultTransferSyntaxes();

    class CapturingSCP : public DcmSCP {
    public:
        explicit CapturingSCP(const std::string& out) : outputDir(out) {}

        void requestStop() { stopRequested = OFTrue; }

        std::string storedPath() const { return capturedPath; }

    protected:
        OFBool stopAfterCurrentAssociation() override { return stopRequested; }
        OFBool stopAfterConnectionTimeout() override { return stopRequested; }

        OFCondition handleSTORERequest(T_DIMSE_C_StoreRQ& reqMessage,
                                       const T_ASC_PresentationContextID presID,
                                       DcmDataset*& reqDataset) override {
            OFCondition receiveStatus = receiveSTORERequest(reqMessage, presID, reqDataset);
            Uint16 rspStatus = checkSTORERequest(reqMessage, reqDataset);

            if (receiveStatus.good() && reqDataset != nullptr) {
                DcmFileFormat storedCopy(reqDataset, OFTrue); // deep copy so we can safely delete reqDataset
                const std::string outPath = JoinPath(outputDir, "dcmtk_store_received.dcm");
                if (storedCopy.saveFile(outPath.c_str()).good()) {
                    capturedPath = outPath;
                } else {
                    rspStatus = STATUS_STORE_Refused_OutOfResources;
                }
            } else {
                rspStatus = STATUS_STORE_Error_CannotUnderstand;
            }

            sendSTOREResponse(presID, reqMessage, rspStatus);
            delete reqDataset;
            reqDataset = nullptr;
            return receiveStatus;
        }

    private:
        std::string outputDir;
        OFBool stopRequested{OFTrue};
        std::string capturedPath;
    };

    CapturingSCP scp(outputDir);
    scp.setAETitle("DTSCP");
    scp.setRespondWithCalledAETitle(OFTrue);
    scp.setPort(0); // let OS pick an available port
    scp.setConnectionBlockingMode(DUL_BLOCK);
    scp.setConnectionTimeout(5);
    scp.setACSETimeout(10);
    scp.setDIMSETimeout(10);
    scp.setMaxReceivePDULength(ASC_DEFAULTMAXPDU);
    scp.setEnableVerification();
    scp.addPresentationContext(sopClass, syntaxes);

    OFCondition openStatus = scp.openListenPort();
    if (openStatus.bad()) {
        std::cerr << "Failed to open SCP port: " << openStatus.text() << std::endl;
        return;
    }
    const Uint16 boundPort = scp.getPort();

    std::thread serverThread([&scp]() {
        scp.acceptAssociations();
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(150));

    DcmSCU scu;
    scu.setAETitle("DTSCU");
    scu.setPeerAETitle("DTSCP");
    scu.setPeerHostName("127.0.0.1");
    scu.setPeerPort(boundPort);
    scu.setACSETimeout(5);
    scu.setDIMSETimeout(10);
    scu.setMaxReceivePDULength(ASC_DEFAULTMAXPDU);
    scu.addPresentationContext(UID_VerificationSOPClass, syntaxes);
    scu.addPresentationContext(sopClass, syntaxes);

    OFCondition initStatus = scu.initNetwork();
    OFCondition assocStatus = initStatus.good() ? scu.negotiateAssociation() : initStatus;
    Uint16 storeStatus = 0;
    OFCondition echoStatus = EC_IllegalCall;
    OFCondition storeCond = EC_IllegalCall;

    if (assocStatus.good()) {
        echoStatus = scu.sendECHORequest(0);
        storeCond = scu.sendSTORERequest(0, OFFilename(filename.c_str()), nullptr, storeStatus);
        scu.closeAssociation(DCMSCU_RELEASE_ASSOCIATION);
    } else {
        std::cerr << "Association negotiation failed: " << assocStatus.text() << std::endl;
    }

    scp.requestStop();
    if (serverThread.joinable()) {
        serverThread.join();
    }

    const std::string reportPath = JoinPath(outputDir, "dcmtk_network_report.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    if (!report.is_open()) {
        std::cerr << "Failed to open network report at: " << reportPath << std::endl;
        return;
    }

    report << "Echo=" << (echoStatus.good() ? "OK" : echoStatus.text()) << "\n";
    report << "StoreStatusCode=" << storeStatus << "\n";
    report << "StoreCondition=" << (storeCond.good() ? "OK" : storeCond.text()) << "\n";

    const std::string storedPath = scp.storedPath();
    if (!storedPath.empty()) {
        report << "StoredFile=" << storedPath << "\n";
        DcmFileFormat stored;
        if (stored.loadFile(storedPath.c_str()).good()) {
            DcmDataset* storedDS = stored.getDataset();
            OFString storedSOPInstance;
            storedDS->findAndGetOFString(DCM_SOPInstanceUID, storedSOPInstance);
            report << "SOPInstanceMatch=" << (storedSOPInstance == sopInstance ? "yes" : "no") << "\n";

            const Uint8* srcData = nullptr;
            const Uint8* storedData = nullptr;
            unsigned long srcLen = 0;
            unsigned long storedLen = 0;
            inputDataset->findAndGetUint8Array(DCM_PixelData, srcData, &srcLen);
            storedDS->findAndGetUint8Array(DCM_PixelData, storedData, &storedLen);
            report << "PixelLengthSrc=" << srcLen << "\n";
            report << "PixelLengthStored=" << storedLen << "\n";
            report << "PixelLengthMatch=" << ((srcLen > 0 && srcLen == storedLen) ? "yes" : "no") << "\n";
        } else {
            report << "StoredFileRead=failed\n";
        }
    } else {
        report << "StoredFile=(none)\n";
    }
    report.close();
    std::cout << "Loopback echo/store test completed (report: " << reportPath << ")" << std::endl;
#else
    (void)filename;
    (void)outputDir;
    std::cout << "DCMTK not enabled." << std::endl;
#endif
}
