/* This work is licensed under a Creative Commons CCZero 1.0 Universal License.
 * See http://creativecommons.org/publicdomain/zero/1.0/ for more information. */

#include <open62541/server.h>
#include <open62541/server_config_default.h>
#include <open62541/plugin/log_stdout.h>
#include <open62541/server_config_file_based.h>
#include <open62541/plugin/certificategroup_default.h>
#include <open62541/common.h>

#include <stdlib.h>
#include "common.h"

int main(int argc, char** argv) {
    UA_ByteString json_config = UA_BYTESTRING_NULL;
    UA_StatusCode retval = UA_STATUSCODE_GOOD;

    if(argc >= 2) {
        /* Load server config */
        json_config = loadFile(argv[1]);
    } else {
        UA_LOG_FATAL(UA_Log_Stdout, UA_LOGCATEGORY_APPLICATION,
                     "Missing argument. Argument are "
                     "<server-config.json5>");
        return EXIT_FAILURE;
    }

    /* Alternative API function */
    UA_Server *server = UA_Server_new();
    UA_ServerConfig *config = UA_Server_getConfig(server);
    UA_ServerConfig_setDefault(config);
    retval = UA_ServerConfig_updateFromFile(config, json_config);
    if(retval != UA_STATUSCODE_GOOD) {
        UA_Server_delete(server);
        return EXIT_FAILURE;
    }

//    UA_Server *server = UA_Server_newFromFile(json_config);
//    UA_ServerConfig *config = UA_Server_getConfig(server);
    config->allowAllCertificateUris = UA_RULEHANDLING_ACCEPT;

    /* Load server certificate and private key */
    UA_ByteString certificate = loadFile("./open62541_server_cert.der");
    UA_ByteString privateKey = loadFile("./open62541_server_key.pem");
    if(certificate.length > 0 && privateKey.length > 0) {
        /* Set certificate for all endpoints */
        for(size_t i = 0; i < config->endpointsSize; i++) {
            UA_ByteString_clear(&config->endpoints[i].serverCertificate);
            UA_ByteString_copy(&certificate, &config->endpoints[i].serverCertificate);
        }
    } else {
        UA_LOG_WARNING(UA_Log_Stdout, UA_LOGCATEGORY_SERVER,
                      "Certificate or private key not found, running without security");
    }
    UA_ByteString_clear(&certificate);
    UA_ByteString_clear(&privateKey);

    /* Add a sample folder and variables for browsing */
    UA_ObjectAttributes folderAttr = UA_ObjectAttributes_default;
    folderAttr.displayName = UA_LOCALIZEDTEXT("en-US", "PS");
    UA_NodeId folderId = UA_NODEID_STRING(1, "PS");
    UA_Server_addObjectNode(server, folderId,
                            UA_NS0ID(OBJECTSFOLDER),
                            UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "PS"),
                            UA_NS0ID(FOLDERTYPE),
                            folderAttr, NULL, NULL);

    /* Feedback folder for end signals */
    UA_ObjectAttributes feedbackAttr = UA_ObjectAttributes_default;
    feedbackAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Feedback");
    UA_NodeId feedbackFolderId = UA_NODEID_STRING(1, "Feedback");
    UA_Server_addObjectNode(server, feedbackFolderId,
                            UA_NS0ID(OBJECTSFOLDER),
                            UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "Feedback"),
                            UA_NS0ID(FOLDERTYPE),
                            feedbackAttr, NULL, NULL);

    /* Trigger folder for start signals */
    UA_ObjectAttributes triggerAttr = UA_ObjectAttributes_default;
    triggerAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Trigger");
    UA_NodeId triggerFolderId = UA_NODEID_STRING(1, "Trigger");
    UA_Server_addObjectNode(server, triggerFolderId,
                            UA_NS0ID(OBJECTSFOLDER),
                            UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "Trigger"),
                            UA_NS0ID(FOLDERTYPE),
                            triggerAttr, NULL, NULL);

    /* Add new Trigger boolean variables under Trigger */
    UA_Boolean op1_1StartValue = false; UA_VariableAttributes op1_1StartAttr = UA_VariableAttributes_default;
    op1_1StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op1_1Start"); op1_1StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op1_1StartAttr.value, &op1_1StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op1_1StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op1_1StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op1_1Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op1_1Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op1_1StartAttr, NULL, NULL);

    UA_Boolean op2_1StartValue = false; UA_VariableAttributes op2_1StartAttr = UA_VariableAttributes_default;
    op2_1StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_1Start"); op2_1StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_1StartAttr.value, &op2_1StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_1StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_1StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_1Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_1Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_1StartAttr, NULL, NULL);

    UA_Boolean op2_2StartValue = false; UA_VariableAttributes op2_2StartAttr = UA_VariableAttributes_default;
    op2_2StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_2Start"); op2_2StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_2StartAttr.value, &op2_2StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_2StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_2StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_2Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_2Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_2StartAttr, NULL, NULL);

    UA_Boolean op2_3StartValue = false; UA_VariableAttributes op2_3StartAttr = UA_VariableAttributes_default;
    op2_3StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_3Start"); op2_3StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_3StartAttr.value, &op2_3StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_3StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_3StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_3Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_3Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_3StartAttr, NULL, NULL);

    UA_Boolean op2_4StartValue = false; UA_VariableAttributes op2_4StartAttr = UA_VariableAttributes_default;
    op2_4StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_4Start"); op2_4StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_4StartAttr.value, &op2_4StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_4StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_4StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_4Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_4Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_4StartAttr, NULL, NULL);

    UA_Boolean op2_5StartValue = false; UA_VariableAttributes op2_5StartAttr = UA_VariableAttributes_default;
    op2_5StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_5Start"); op2_5StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_5StartAttr.value, &op2_5StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_5StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_5StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_5Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_5Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_5StartAttr, NULL, NULL);

    UA_Boolean op2_6StartValue = false; UA_VariableAttributes op2_6StartAttr = UA_VariableAttributes_default;
    op2_6StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_6Start"); op2_6StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_6StartAttr.value, &op2_6StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_6StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_6StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_6Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_6Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_6StartAttr, NULL, NULL);

    UA_Boolean op2_7StartValue = false; UA_VariableAttributes op2_7StartAttr = UA_VariableAttributes_default;
    op2_7StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op2_7Start"); op2_7StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2_7StartAttr.value, &op2_7StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2_7StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2_7StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op2_7Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op2_7Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op2_7StartAttr, NULL, NULL);

    UA_Boolean op3_1StartValue = false; UA_VariableAttributes op3_1StartAttr = UA_VariableAttributes_default;
    op3_1StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op3_1Start"); op3_1StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3_1StartAttr.value, &op3_1StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3_1StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3_1StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op3_1Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op3_1Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op3_1StartAttr, NULL, NULL);

    UA_Boolean op3_2StartValue = false; UA_VariableAttributes op3_2StartAttr = UA_VariableAttributes_default;
    op3_2StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op3_2Start"); op3_2StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3_2StartAttr.value, &op3_2StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3_2StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3_2StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op3_2Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op3_2Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op3_2StartAttr, NULL, NULL);

    UA_Boolean op3_3StartValue = false; UA_VariableAttributes op3_3StartAttr = UA_VariableAttributes_default;
    op3_3StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op3_3Start"); op3_3StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3_3StartAttr.value, &op3_3StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3_3StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3_3StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op3_3Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op3_3Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op3_3StartAttr, NULL, NULL);

    UA_Boolean op3_4StartValue = false; UA_VariableAttributes op3_4StartAttr = UA_VariableAttributes_default;
    op3_4StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op3_4Start"); op3_4StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3_4StartAttr.value, &op3_4StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3_4StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3_4StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op3_4Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op3_4Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op3_4StartAttr, NULL, NULL);

    UA_Boolean op3_5StartValue = false; UA_VariableAttributes op3_5StartAttr = UA_VariableAttributes_default;
    op3_5StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op3_5Start"); op3_5StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3_5StartAttr.value, &op3_5StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3_5StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3_5StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op3_5Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op3_5Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op3_5StartAttr, NULL, NULL);

    UA_Boolean op4_1StartValue = false; UA_VariableAttributes op4_1StartAttr = UA_VariableAttributes_default;
    op4_1StartAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Op4_1Start"); op4_1StartAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op4_1StartAttr.value, &op4_1StartValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op4_1StartAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op4_1StartAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.Op4_1Start"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Op4_1Start"), UA_NS0ID(BASEDATAVARIABLETYPE), op4_1StartAttr, NULL, NULL);

    UA_Boolean firstOpValue = false; UA_VariableAttributes firstOpAttr = UA_VariableAttributes_default;
    firstOpAttr.displayName = UA_LOCALIZEDTEXT("en-US", "FirstOp"); firstOpAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&firstOpAttr.value, &firstOpValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    firstOpAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; firstOpAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.FirstOp"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "FirstOp"), UA_NS0ID(BASEDATAVARIABLETYPE), firstOpAttr, NULL, NULL);

    UA_Boolean secondOpValue = false; UA_VariableAttributes secondOpAttr = UA_VariableAttributes_default;
    secondOpAttr.displayName = UA_LOCALIZEDTEXT("en-US", "SecondOp"); secondOpAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&secondOpAttr.value, &secondOpValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    secondOpAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; secondOpAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.SecondOp"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "SecondOp"), UA_NS0ID(BASEDATAVARIABLETYPE), secondOpAttr, NULL, NULL);

    UA_Boolean thridOpValue = false; UA_VariableAttributes thridOpAttr = UA_VariableAttributes_default;
    thridOpAttr.displayName = UA_LOCALIZEDTEXT("en-US", "ThridOp"); thridOpAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&thridOpAttr.value, &thridOpValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    thridOpAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; thridOpAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.ThridOp"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "ThridOp"), UA_NS0ID(BASEDATAVARIABLETYPE), thridOpAttr, NULL, NULL);

    UA_Boolean fourthOpValue = false; UA_VariableAttributes fourthOpAttr = UA_VariableAttributes_default;
    fourthOpAttr.displayName = UA_LOCALIZEDTEXT("en-US", "FourthOp"); fourthOpAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&fourthOpAttr.value, &fourthOpValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    fourthOpAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; fourthOpAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Trigger.FourthOp"), triggerFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "FourthOp"), UA_NS0ID(BASEDATAVARIABLETYPE), fourthOpAttr, NULL, NULL);

    /* Add Op1..Op6 ending-signal boolean variables under Feedback */
    UA_Boolean op1EndValue = false; UA_VariableAttributes op1EndAttr = UA_VariableAttributes_default;
    op1EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Sauggreifer_end_1"); op1EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op1EndAttr.value, &op1EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op1EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op1EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Sauggreifer_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Sauggreifer_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op1EndAttr, NULL, NULL);

    UA_Boolean op2EndValue = false; UA_VariableAttributes op2EndAttr = UA_VariableAttributes_default;
    op2EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APP_HL_end_1"); op2EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op2EndAttr.value, &op2EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op2EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op2EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HL_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APP_HL_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op2EndAttr, NULL, NULL);

    UA_Boolean op3EndValue = false; UA_VariableAttributes op3EndAttr = UA_VariableAttributes_default;
    op3EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_end_1_1"); op3EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op3EndAttr.value, &op3EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op3EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op3EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_end_1_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_end_1_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op3EndAttr, NULL, NULL);

    UA_Boolean op4EndValue = false; UA_VariableAttributes op4EndAttr = UA_VariableAttributes_default;
    op4EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_2"); op4EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op4EndAttr.value, &op4EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op4EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op4EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_2"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_2"), UA_NS0ID(BASEDATAVARIABLETYPE), op4EndAttr, NULL, NULL);

    UA_Boolean op5EndValue = false; UA_VariableAttributes op5EndAttr = UA_VariableAttributes_default;
    op5EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1_1"); op5EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op5EndAttr.value, &op5EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op5EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op5EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op5EndAttr, NULL, NULL);

    UA_Boolean op6EndValue = false; UA_VariableAttributes op6EndAttr = UA_VariableAttributes_default;
    op6EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end_1"); op6EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op6EndAttr.value, &op6EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op6EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op6EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op6EndAttr, NULL, NULL);

    /* Additional Feedback signals */
    UA_Boolean op7EndValue = false; UA_VariableAttributes op7EndAttr = UA_VariableAttributes_default;
    op7EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Sauggreifer_Original_end"); op7EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op7EndAttr.value, &op7EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op7EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op7EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Sauggreifer_Original_end"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Sauggreifer_Original_end"), UA_NS0ID(BASEDATAVARIABLETYPE), op7EndAttr, NULL, NULL);

    UA_Boolean op8EndValue = false; UA_VariableAttributes op8EndAttr = UA_VariableAttributes_default;
    op8EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Enclosure_Op_end_1"); op8EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op8EndAttr.value, &op8EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op8EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op8EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Enclosure_Op_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Enclosure_Op_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op8EndAttr, NULL, NULL);

    UA_Boolean op9EndValue = false; UA_VariableAttributes op9EndAttr = UA_VariableAttributes_default;
    op9EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APP_HL_end"); op9EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op9EndAttr.value, &op9EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op9EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op9EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APP_HL_end"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APP_HL_end"), UA_NS0ID(BASEDATAVARIABLETYPE), op9EndAttr, NULL, NULL);

    UA_Boolean op10EndValue = false; UA_VariableAttributes op10EndAttr = UA_VariableAttributes_default;
    op10EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_end_1"); op10EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op10EndAttr.value, &op10EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op10EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op10EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op10EndAttr, NULL, NULL);

    UA_Boolean op11EndValue = false; UA_VariableAttributes op11EndAttr = UA_VariableAttributes_default;
    op11EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1"); op11EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op11EndAttr.value, &op11EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op11EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op11EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op11EndAttr, NULL, NULL);

    UA_Boolean op12EndValue = false; UA_VariableAttributes op12EndAttr = UA_VariableAttributes_default;
    op12EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1"); op12EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op12EndAttr.value, &op12EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op12EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op12EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_APPROACH_HL_end_1_1"), UA_NS0ID(BASEDATAVARIABLETYPE), op12EndAttr, NULL, NULL);

    UA_Boolean op13EndValue = false; UA_VariableAttributes op13EndAttr = UA_VariableAttributes_default;
    op13EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end"); op13EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op13EndAttr.value, &op13EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op13EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op13EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Gen_Rob_Op_Lukas_LSI_600_DEP_HR_end"), UA_NS0ID(BASEDATAVARIABLETYPE), op13EndAttr, NULL, NULL);

    UA_Boolean op14EndValue = false; UA_VariableAttributes op14EndAttr = UA_VariableAttributes_default;
    op14EndAttr.displayName = UA_LOCALIZEDTEXT("en-US", "Enclosure_Op_end"); op14EndAttr.dataType = UA_TYPES[UA_TYPES_BOOLEAN].typeId;
    UA_Variant_setScalar(&op14EndAttr.value, &op14EndValue, &UA_TYPES[UA_TYPES_BOOLEAN]);
    op14EndAttr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; op14EndAttr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "Feedback.Enclosure_Op_end"), feedbackFolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "Enclosure_Op_end"), UA_NS0ID(BASEDATAVARIABLETYPE), op14EndAttr, NULL, NULL);

    /* ========================================================================
     * OPC UA VARIABLES - Add your variables below
     * ========================================================================
     * Each variable needs:
     * 1. A value variable (e.g., UA_Boolean, UA_Int32, UA_Double)
     * 2. A UA_VariableAttributes struct with:
     *    - displayName: Name shown in OPC UA clients
     *    - dataType: The OPC UA type ID
     *    - value: Initial value set via UA_Variant_setScalar
     *    - accessLevel & userAccessLevel: Read/Write permissions
     * 3. Call UA_Server_addVariableNode with:
     *    - NodeId: Unique identifier (e.g., "PS.VariableName")
     *    - Parent: folderId (the PS folder)
     *    - BrowseName: Name for browsing
     *
     * ======================================================================== */

    /* (Removed non-robot variables: Enabled, Start, Value, ValueReal, Joint_*) */

    /* Create Robot folders under PS and add joints j1..j6 to each robot */
    /* PS.Robot1 */
    UA_ObjectAttributes robot1Attr = UA_ObjectAttributes_default;
    robot1Attr.displayName = UA_LOCALIZEDTEXT("en-US", "Robot1");
    UA_NodeId robot1FolderId = UA_NODEID_STRING(1, "PS.Robot1");
    UA_Server_addObjectNode(server, robot1FolderId,
                            folderId, UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "Robot1"),
                            UA_NS0ID(FOLDERTYPE),
                            robot1Attr, NULL, NULL);

    /* j1..j6 for Robot1 */
    UA_Double robot1_j1Value = 0.0; UA_VariableAttributes robot1_j1Attr = UA_VariableAttributes_default;
    robot1_j1Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j1"); robot1_j1Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j1Attr.value, &robot1_j1Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j1Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j1Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j1"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j1"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j1Attr, NULL, NULL);

    UA_Double robot1_j2Value = 0.0; UA_VariableAttributes robot1_j2Attr = UA_VariableAttributes_default;
    robot1_j2Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j2"); robot1_j2Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j2Attr.value, &robot1_j2Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j2Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j2Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j2"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j2"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j2Attr, NULL, NULL);

    UA_Double robot1_j3Value = 0.0; UA_VariableAttributes robot1_j3Attr = UA_VariableAttributes_default;
    robot1_j3Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j3"); robot1_j3Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j3Attr.value, &robot1_j3Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j3Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j3Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j3"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j3"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j3Attr, NULL, NULL);

    UA_Double robot1_j4Value = 0.0; UA_VariableAttributes robot1_j4Attr = UA_VariableAttributes_default;
    robot1_j4Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j4"); robot1_j4Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j4Attr.value, &robot1_j4Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j4Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j4Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j4"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j4"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j4Attr, NULL, NULL);

    UA_Double robot1_j5Value = 0.0; UA_VariableAttributes robot1_j5Attr = UA_VariableAttributes_default;
    robot1_j5Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j5"); robot1_j5Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j5Attr.value, &robot1_j5Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j5Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j5Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j5"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j5"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j5Attr, NULL, NULL);

    UA_Double robot1_j6Value = 0.0; UA_VariableAttributes robot1_j6Attr = UA_VariableAttributes_default;
    robot1_j6Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j6"); robot1_j6Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot1_j6Attr.value, &robot1_j6Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot1_j6Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot1_j6Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot1.j6"), robot1FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j6"), UA_NS0ID(BASEDATAVARIABLETYPE), robot1_j6Attr, NULL, NULL);

    /* PS.Robot2 */
    UA_ObjectAttributes robot2Attr = UA_ObjectAttributes_default;
    robot2Attr.displayName = UA_LOCALIZEDTEXT("en-US", "Robot2");
    UA_NodeId robot2FolderId = UA_NODEID_STRING(1, "PS.Robot2");
    UA_Server_addObjectNode(server, robot2FolderId,
                            folderId, UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "Robot2"),
                            UA_NS0ID(FOLDERTYPE),
                            robot2Attr, NULL, NULL);

    /* j1..j6 for Robot2 */
    UA_Double robot2_j1Value = 0.0; UA_VariableAttributes robot2_j1Attr = UA_VariableAttributes_default;
    robot2_j1Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j1"); robot2_j1Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j1Attr.value, &robot2_j1Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j1Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j1Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j1"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j1"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j1Attr, NULL, NULL);

    UA_Double robot2_j2Value = 0.0; UA_VariableAttributes robot2_j2Attr = UA_VariableAttributes_default;
    robot2_j2Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j2"); robot2_j2Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j2Attr.value, &robot2_j2Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j2Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j2Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j2"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j2"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j2Attr, NULL, NULL);

    UA_Double robot2_j3Value = 0.0; UA_VariableAttributes robot2_j3Attr = UA_VariableAttributes_default;
    robot2_j3Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j3"); robot2_j3Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j3Attr.value, &robot2_j3Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j3Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j3Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j3"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j3"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j3Attr, NULL, NULL);

    UA_Double robot2_j4Value = 0.0; UA_VariableAttributes robot2_j4Attr = UA_VariableAttributes_default;
    robot2_j4Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j4"); robot2_j4Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j4Attr.value, &robot2_j4Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j4Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j4Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j4"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j4"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j4Attr, NULL, NULL);

    UA_Double robot2_j5Value = 0.0; UA_VariableAttributes robot2_j5Attr = UA_VariableAttributes_default;
    robot2_j5Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j5"); robot2_j5Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j5Attr.value, &robot2_j5Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j5Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j5Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j5"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j5"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j5Attr, NULL, NULL);

    UA_Double robot2_j6Value = 0.0; UA_VariableAttributes robot2_j6Attr = UA_VariableAttributes_default;
    robot2_j6Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j6"); robot2_j6Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot2_j6Attr.value, &robot2_j6Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot2_j6Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot2_j6Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot2.j6"), robot2FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j6"), UA_NS0ID(BASEDATAVARIABLETYPE), robot2_j6Attr, NULL, NULL);

    /* PS.Robot3 */
    UA_ObjectAttributes robot3Attr = UA_ObjectAttributes_default;
    robot3Attr.displayName = UA_LOCALIZEDTEXT("en-US", "Robot3");
    UA_NodeId robot3FolderId = UA_NODEID_STRING(1, "PS.Robot3");
    UA_Server_addObjectNode(server, robot3FolderId,
                            folderId, UA_NS0ID(ORGANIZES),
                            UA_QUALIFIEDNAME(1, "Robot3"),
                            UA_NS0ID(FOLDERTYPE),
                            robot3Attr, NULL, NULL);

    /* j1..j6 for Robot3 */
    UA_Double robot3_j1Value = 0.0; UA_VariableAttributes robot3_j1Attr = UA_VariableAttributes_default;
    robot3_j1Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j1"); robot3_j1Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j1Attr.value, &robot3_j1Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j1Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j1Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j1"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j1"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j1Attr, NULL, NULL);

    UA_Double robot3_j2Value = 0.0; UA_VariableAttributes robot3_j2Attr = UA_VariableAttributes_default;
    robot3_j2Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j2"); robot3_j2Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j2Attr.value, &robot3_j2Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j2Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j2Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j2"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j2"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j2Attr, NULL, NULL);

    UA_Double robot3_j3Value = 0.0; UA_VariableAttributes robot3_j3Attr = UA_VariableAttributes_default;
    robot3_j3Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j3"); robot3_j3Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j3Attr.value, &robot3_j3Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j3Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j3Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j3"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j3"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j3Attr, NULL, NULL);

    UA_Double robot3_j4Value = 0.0; UA_VariableAttributes robot3_j4Attr = UA_VariableAttributes_default;
    robot3_j4Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j4"); robot3_j4Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j4Attr.value, &robot3_j4Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j4Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j4Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j4"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j4"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j4Attr, NULL, NULL);

    UA_Double robot3_j5Value = 0.0; UA_VariableAttributes robot3_j5Attr = UA_VariableAttributes_default;
    robot3_j5Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j5"); robot3_j5Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j5Attr.value, &robot3_j5Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j5Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j5Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j5"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j5"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j5Attr, NULL, NULL);

    UA_Double robot3_j6Value = 0.0; UA_VariableAttributes robot3_j6Attr = UA_VariableAttributes_default;
    robot3_j6Attr.displayName = UA_LOCALIZEDTEXT("en-US", "j6"); robot3_j6Attr.dataType = UA_TYPES[UA_TYPES_DOUBLE].typeId;
    UA_Variant_setScalar(&robot3_j6Attr.value, &robot3_j6Value, &UA_TYPES[UA_TYPES_DOUBLE]);
    robot3_j6Attr.accessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE; robot3_j6Attr.userAccessLevel = UA_ACCESSLEVELMASK_READ | UA_ACCESSLEVELMASK_WRITE;
    UA_Server_addVariableNode(server, UA_NODEID_STRING(1, "PS.Robot3.j6"), robot3FolderId, UA_NS0ID(ORGANIZES), UA_QUALIFIEDNAME(1, "j6"), UA_NS0ID(BASEDATAVARIABLETYPE), robot3_j6Attr, NULL, NULL);

    retval = UA_Server_runUntilInterrupt(server);
    retval |= UA_Server_delete(server);

    /* clean up */
    UA_ByteString_clear(&json_config);

    return retval == UA_STATUSCODE_GOOD ? EXIT_SUCCESS : EXIT_FAILURE;
}

/* run in elevated PowerShell
New-NetFirewallRule -DisplayName "OPC UA 4841" -Direction Inbound -LocalPort 4841 -Protocol TCP -Action Allow
*/
