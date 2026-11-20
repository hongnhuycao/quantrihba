Attribute VB_Name = "ClaudeExcel"
'==============================================================================
' ClaudeExcel - Ket noi truc tiep Claude (Anthropic API) vao Excel
'
' Cach dung nhanh (xem them HUONG_DAN.md):
'   1. Chay macro  CaiDatApiKey  -> dan API key (sk-ant-...) mot lan.
'   2. Trong o bat ky:  =CLAUDE("Tom tat noi dung sau"; A2:D20)
'   3. Macro  HoiClaudeVeVungChon : hoi Claude ve vung dang chon, ket qua ra sheet moi.
'   4. Macro  ClaudeXuLyTungO     : ap 1 yeu cau cho tung o trong vung chon,
'                                   ket qua ghi vao cot ben phai.
'
' Yeu cau: Excel cho Windows (dung MSXML2 + ADODB co san trong Windows).
' File nay chi dung ky tu ASCII de VBA Editor khong bi loi font.
'==============================================================================
Option Explicit

#If VBA7 Then
Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#Else
Private Declare Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#End If

'----------------------------- CAU HINH ---------------------------------------
Private Const API_URL As String = "https://api.anthropic.com/v1/messages"
Private Const API_VERSION As String = "2026-10-21"
' Model mac dinh. Muon nhanh/re hon co the doi sang "claude-sonnet-5-5"
' hoac "claude-haiku-5-5", hoac truyen model rieng trong ham =CLAUDE(...).
Public Const MODEL_MAC_DINH As String = "claude-opus-5-5"
Private Const MAX_TOKENS As Long = 16000
' Muc "suy nghi": low | medium | high | xhigh | max.
' "low" cho tra loi nhanh, hop voi cong viec trong o Excel (phan loai, tom tat,
' trich xuat). Tang len "medium"/"high" cho bai toan phuc tap.
Private Const EFFORT As String = "low"
Private Const TIMEOUT_MS As Long = 300000      ' 5 phut cho moi lan goi
Private Const SO_LAN_THU_LAI As Long = 3
Private Const APP_NAME As String = "ClaudeExcel"
Private Const GIOI_HAN_O As Long = 32767       ' gioi han ky tu cua 1 o Excel

Private Const SYSTEM_O As String = _
    "Ban la tro ly chay ben trong mot o Excel. Chi tra ve ket qua cuoi cung, " & _
    "ngan gon, khong giai thich, khong chao hoi, khong dung markdown. " & _
    "Tra loi bang ngon ngu cua yeu cau (tieng Viet thi viet co dau day du)."

Private Const SYSTEM_BANG As String = _
    "Ban la tro ly phan tich du lieu cho nguoi dung Excel. Khong dung markdown " & _
    "(khong **, khong #, khong ```). Neu cau tra loi co dang bang, hay tra ve " & _
    "bang dang TSV: moi dong mot hang, cac cot cach nhau bang ky tu TAB, dong dau " & _
    "la tieu de. So lieu viet dang so thuan (vd 1234567.5), khong dau phan cach " & _
    "hang nghin, khong kem don vi trong o so. Tra loi bang ngon ngu cua cau hoi (tieng Viet thi co dau day du)."

' Bo nho dem: cung yeu cau + du lieu thi khong goi lai API (tiet kiem chi phi
' khi Excel tinh lai cong thuc).
Private mCache As Object

' Bien dung cho bo doc JSON
Private mJ As String
Private mP As Long

'==============================================================================
'                       HAM DUNG TRONG O EXCEL
'==============================================================================

' =CLAUDE(yeu_cau; [du_lieu]; [model])
'   yeu_cau : cau lenh / cau hoi (chu hoac o chua chu)
'   du_lieu : (tuy chon) vung o, gia tri hoac mang dua kem cho Claude doc
'   model   : (tuy chon) vd "claude-haiku-5-5"
Public Function CLAUDE(ByVal yeu_cau As Variant, Optional ByVal du_lieu As Variant, _
                       Optional ByVal model As String = "") As Variant
    On Error GoTo Loi

    ' Khong goi API khi dang mo hop thoai Insert Function (tranh ton tien).
    If DangMoFunctionWizard() Then
        CLAUDE = "(Claude se chay khi bam Enter)"
        Exit Function
    End If

    Dim prompt As String
    prompt = GiaTriThanhChu(yeu_cau)
    If Len(Trim$(prompt)) = 0 Then
        CLAUDE = ""
        Exit Function
    End If

    If Not IsMissing(du_lieu) Then
        Dim duLieuText As String
        duLieuText = GiaTriThanhChu(du_lieu)
        If Len(duLieuText) > 0 Then
            prompt = prompt & vbLf & vbLf & "<du_lieu>" & vbLf & duLieuText & vbLf & "</du_lieu>"
        End If
    End If

    If Len(model) = 0 Then model = MODEL_MAC_DINH

    Dim khoa As String
    khoa = model & ChrW$(0) & SYSTEM_O & ChrW$(0) & prompt
    If mCache Is Nothing Then Set mCache = CreateObject("Scripting.Dictionary")
    If mCache.Exists(khoa) Then
        CLAUDE = mCache(khoa)
        Exit Function
    End If

    Dim kq As String
    kq = GoiClaude(prompt, SYSTEM_O, model)
    kq = CatChoVuaO(kq)
    mCache(khoa) = kq
    CLAUDE = kq
    Exit Function
Loi:
    CLAUDE = "#CLAUDE: " & Err.Description
End Function

'==============================================================================
'                              MACRO
'==============================================================================

' Luu API key vao Windows (Registry cua user hien tai), KHONG luu trong file
' Excel -> gui file cho nguoi khac cung khong lo key.
Public Sub CaiDatApiKey()
    Dim k As String
    k = InputBox("Dan Anthropic API key (bat dau bang sk-ant-...)." & vbLf & _
                 "Lay key tai: console.anthropic.com > API Keys", APP_NAME)
    k = Trim$(k)
    If Len(k) = 0 Then Exit Sub
    SaveSetting APP_NAME, "Config", "ApiKey", k
    MsgBox "Da luu API key. Thu go vao 1 o:  =CLAUDE(""Xin chao"")", vbInformation, APP_NAME
End Sub

Public Sub XoaApiKey()
    On Error Resume Next
    DeleteSetting APP_NAME, "Config", "ApiKey"
    MsgBox "Da xoa API key khoi may nay.", vbInformation, APP_NAME
End Sub

' Xoa bo nho dem -> lan tinh lai sau se goi Claude moi.
Public Sub XoaBoNhoDem()
    Set mCache = Nothing
    MsgBox "Da xoa bo nho dem. Bam Ctrl+Alt+F9 de tinh lai toan bo.", vbInformation, APP_NAME
End Sub

' Hoi Claude ve vung dang chon; ket qua (chu hoac bang) ghi ra sheet moi.
Public Sub HoiClaudeVeVungChon()
    On Error GoTo Loi
    Dim vung As Range, diaChi As String
    If TypeName(Selection) = "Range" Then
        Set vung = Selection
        diaChi = " (" & vung.Address(False, False) & ")"
    End If

    Dim cauHoi As String
    cauHoi = InputBox("Ban muon hoi Claude gi ve vung dang chon" & diaChi & "?" & vbLf & vbLf & _
        "Vd: Tong hop cong no theo chu dau tu; Tim cac dong bat thuong; Lap bang ke...", APP_NAME)
    If Len(Trim$(cauHoi)) = 0 Then Exit Sub

    Dim prompt As String
    prompt = cauHoi
    If Not vung Is Nothing Then
        If Application.WorksheetFunction.CountA(vung) > 0 Then
            prompt = prompt & vbLf & vbLf & "<du_lieu sheet=""" & vung.Worksheet.Name & _
                     """ vung=""" & vung.Address(False, False) & """>" & vbLf & _
                     GiaTriThanhChu(vung) & vbLf & "</du_lieu>"
        End If
    End If

    Application.StatusBar = "Claude dang tra loi..."
    Application.Cursor = xlWait
    Dim kq As String
    kq = GoiClaude(prompt, SYSTEM_BANG, MODEL_MAC_DINH)
    Application.Cursor = xlDefault
    Application.StatusBar = False

    Dim ws As Worksheet
    Set ws = ActiveWorkbook.Worksheets.Add(After:=ActiveWorkbook.Sheets(ActiveWorkbook.Sheets.Count))
    On Error Resume Next
    ws.Name = "Claude " & Format(Now, "ddmm hhnnss")
    On Error GoTo Loi

    ws.Range("A1").Value = "Cau hoi: " & cauHoi
    ws.Range("A1").Font.Bold = True
    GhiChuRaSheet kq, ws.Range("A3")
    ws.Columns.AutoFit
    Dim c As Range
    For Each c In ws.UsedRange.Columns
        If c.ColumnWidth > 80 Then c.ColumnWidth = 80: c.WrapText = True
    Next c
    ws.Activate
    Exit Sub
Loi:
    Application.Cursor = xlDefault
    Application.StatusBar = False
    MsgBox "Loi: " & Err.Description, vbExclamation, APP_NAME
End Sub

' Ap mot yeu cau cho TUNG o trong vung chon. Ket qua ghi dang GIA TRI (khong
' phai cong thuc) vao o ben phai -> khong bi tinh lai, khong ton tien them.
Public Sub ClaudeXuLyTungO()
    On Error GoTo Loi
    If TypeName(Selection) <> "Range" Then
        MsgBox "Hay chon vung o can xu ly truoc.", vbExclamation, APP_NAME
        Exit Sub
    End If
    Dim vung As Range
    Set vung = Selection

    Dim yc As String
    yc = InputBox("Yeu cau ap cho tung o (ket qua ghi vao cot ben phai):" & vbLf & vbLf & _
        "Vd: Phan loai chi phi nay vao: Vat tu / Nhan cong / May / Khac" & vbLf & _
        "    Dich sang tieng Anh" & vbLf & "    Trich ma so thue tu doan van", APP_NAME)
    If Len(Trim$(yc)) = 0 Then Exit Sub

    Dim tong As Long, dem As Long, c As Range
    For Each c In vung.Cells
        If Len(Trim$(CStr(c.Text))) > 0 Then tong = tong + 1
    Next c
    If tong = 0 Then Exit Sub
    If MsgBox("Se goi Claude " & tong & " lan. Tiep tuc?", vbYesNo + vbQuestion, APP_NAME) <> vbYes Then Exit Sub

    Application.EnableCancelKey = xlErrorHandler   ' bam Esc de dung
    For Each c In vung.Cells
        If Len(Trim$(CStr(c.Text))) > 0 Then
            dem = dem + 1
            Application.StatusBar = "Claude dang xu ly " & dem & "/" & tong & " (Esc de dung)..."
            Dim kq As String
            On Error Resume Next
            kq = GoiClaude(yc & vbLf & vbLf & "<noi_dung>" & vbLf & GiaTriThanhChu(c) & _
                           vbLf & "</noi_dung>", SYSTEM_O, MODEL_MAC_DINH)
            If Err.Number = 18 Then On Error GoTo Loi: Err.Raise 18
            If Err.Number <> 0 Then kq = "#CLAUDE: " & Err.Description
            On Error GoTo Loi
            c.Offset(0, 1).Value = CatChoVuaO(kq)
            DoEvents
        End If
    Next c
    Application.StatusBar = False
    MsgBox "Xong " & dem & " o.", vbInformation, APP_NAME
    Exit Sub
Loi:
    Application.StatusBar = False
    If Err.Number = 18 Then
        MsgBox "Da dung theo yeu cau (" & dem & "/" & tong & ").", vbInformation, APP_NAME
    Else
        MsgBox "Loi: " & Err.Description, vbExclamation, APP_NAME
    End If
End Sub

'==============================================================================
'                         GOI API ANTHROPIC
'==============================================================================

' Goi Messages API, tra ve phan chu cua cau tra loi. Loi thi Err.Raise.
Public Function GoiClaude(ByVal userText As String, ByVal systemPrompt As String, _
                          ByVal model As String) As String
    Dim apiKey As String
    apiKey = LayApiKey()
    If Len(apiKey) = 0 Then Err.Raise vbObjectError + 100, APP_NAME, _
        "Chua co API key. Chay macro CaiDatApiKey."

    Dim coFallback As Boolean
    coFallback = HoTroFallback(model)

    Dim body As String
    body = "{""model"":""" & JsonEsc(model) & """" & _
           ",""max_tokens"":" & CStr(MAX_TOKENS) & _
           ",""output_config"":{""effort"":""" & EFFORT & """}" & _
           IIf(coFallback, ",""fallbacks"":""default""", "") & _
           ",""system"":""" & JsonEsc(systemPrompt) & """" & _
           ",""messages"":[{""role"":""user"",""content"":""" & JsonEsc(userText) & """}]}"

    Dim http As Object, lan As Long, status As Long, resp As String
    For lan = 1 To SO_LAN_THU_LAI
        Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
        http.setTimeouts 15000, 30000, 30000, TIMEOUT_MS
        http.Open "POST", API_URL, False
        http.setRequestHeader "content-type", "application/json"
        http.setRequestHeader "x-api-key", apiKey
        http.setRequestHeader "anthropic-version", API_VERSION
        If coFallback Then http.setRequestHeader "anthropic-beta", "server-side-fallback-2026-07-01"
        http.send Utf8Bytes(body)

        status = http.status
        resp = Utf8Text(http.responseBody)
        ' 429 (qua gioi han), 5xx, 529 (qua tai) -> doi roi thu lai
        If status = 429 Or status >= 500 Then
            If lan < SO_LAN_THU_LAI Then Sleep 2000 * lan
        Else
            Exit For
        End If
    Next lan

    Dim j As Object
    If status <> 200 Then
        Dim thongBao As String
        thongBao = "HTTP " & status
        On Error Resume Next
        Set j = ParseJson(resp)
        thongBao = thongBao & " - " & j("error")("message")
        On Error GoTo 0
        Select Case status
            Case 401: thongBao = "API key khong dung (" & thongBao & ")"
            Case 429: thongBao = "Vuot gioi han goi, thu lai sau (" & thongBao & ")"
            Case 529: thongBao = "May chu Claude dang qua tai (" & thongBao & ")"
        End Select
        Err.Raise vbObjectError + 200 + status, APP_NAME, thongBao
    End If

    Set j = ParseJson(resp)
    Dim stopReason As String
    If Not IsNull(j("stop_reason")) Then stopReason = j("stop_reason")

    Dim kq As String, blk As Variant
    For Each blk In j("content")
        If blk("type") = "text" Then kq = kq & blk("text")
    Next blk

    If stopReason = "refusal" Then
        Err.Raise vbObjectError + 300, APP_NAME, "Claude tu choi yeu cau nay"
    ElseIf stopReason = "max_tokens" Then
        kq = kq & " [...bi cat do vuot max_tokens]"
    End If
    GoiClaude = Trim$(kq)
End Function

Private Function LayApiKey() As String
    LayApiKey = Environ$("ANTHROPIC_API_KEY")
    If Len(LayApiKey) = 0 Then LayApiKey = GetSetting(APP_NAME, "Config", "ApiKey", "")
End Function

' Cac model ho tro tu dong chuyen model du phong khi bi tu choi (fallbacks).
Private Function HoTroFallback(ByVal model As String) As Boolean
    Select Case LCase$(model)
        Case "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", _
             "claude-fable-5-2", "claude-fable-5-1"
            HoTroFallback = True
    End Select
End Function

'==============================================================================
'                           TIEN ICH
'==============================================================================

' Chuyen o / vung / mang / gia tri thanh chu (vung -> bang TSV).
Private Function GiaTriThanhChu(ByVal v As Variant) As String
    If TypeName(v) = "Range" Then
        Dim a As Range, out As String, r As Range
        ' Chon ca cot (A:A) -> chi lay phan co du lieu
        Set r = Application.Intersect(v, v.Worksheet.UsedRange)
        If r Is Nothing Then Exit Function
        For Each a In r.Areas
            If Len(out) > 0 Then out = out & vbLf
            out = out & MangThanhChu(a.Value)
        Next a
        GiaTriThanhChu = out
    ElseIf IsArray(v) Then
        GiaTriThanhChu = MangThanhChu(v)
    Else
        GiaTriThanhChu = MotGiaTri(v)
    End If
End Function

Private Function MangThanhChu(ByVal arr As Variant) As String
    If Not IsArray(arr) Then
        MangThanhChu = MotGiaTri(arr)
        Exit Function
    End If
    Dim r As Long, c As Long, dong As String, out As String, hai As Boolean
    On Error Resume Next
    c = LBound(arr, 2)
    hai = (Err.Number = 0)
    On Error GoTo 0
    If hai Then
        For r = LBound(arr, 1) To UBound(arr, 1)
            dong = ""
            For c = LBound(arr, 2) To UBound(arr, 2)
                If c > LBound(arr, 2) Then dong = dong & vbTab
                dong = dong & MotGiaTri(arr(r, c))
            Next c
            If Len(out) > 0 Then out = out & vbLf
            out = out & dong
        Next r
    Else
        For r = LBound(arr) To UBound(arr)
            If r > LBound(arr) Then out = out & vbTab
            out = out & MotGiaTri(arr(r))
        Next r
    End If
    MangThanhChu = out
End Function

Private Function MotGiaTri(ByVal v As Variant) As String
    If IsError(v) Then
        MotGiaTri = "#LOI"
    ElseIf IsEmpty(v) Or IsNull(v) Then
        MotGiaTri = ""
    ElseIf VarType(v) = vbDate Then
        If v = Int(v) Then
            MotGiaTri = Format$(v, "dd/mm/yyyy")
        Else
            MotGiaTri = Format$(v, "dd/mm/yyyy hh:nn")
        End If
    ElseIf IsNumeric(v) And VarType(v) <> vbString Then
        MotGiaTri = Replace(CStr(v), Application.International(xlDecimalSeparator), ".")
    Else
        ' Tab/xuong dong trong o se lam vo bang -> thay bang khoang trang
        MotGiaTri = Replace(Replace(Replace(CStr(v), vbTab, " "), vbCrLf, " "), vbLf, " ")
    End If
End Function

' Ghi chu ra sheet: moi dong 1 hang, TAB -> sang cot.
Private Sub GhiChuRaSheet(ByVal s As String, ByVal batDau As Range)
    Dim dongs() As String, cot() As String, i As Long, k As Long
    s = Replace(s, vbCrLf, vbLf)
    dongs = Split(s, vbLf)
    For i = LBound(dongs) To UBound(dongs)
        cot = Split(dongs(i), vbTab)
        For k = LBound(cot) To UBound(cot)
            Dim o As Range
            Set o = batDau.Offset(i, k)
            If LaSoThuan(cot(k)) Then
                o.Value = Val(cot(k))      ' so -> de SUM/loc duoc
            Else
                o.NumberFormat = "@"       ' giu nguyen chu, khong tu doi thanh ngay
                o.Value = CatChoVuaO(cot(k))
            End If
        Next k
    Next i
End Sub

' So dang 1234 / -1234.5 (khong so 0 dung dau nhu ma "0123").
Private Function LaSoThuan(ByVal s As String) As Boolean
    s = Trim$(s)
    If Len(s) = 0 Or Len(s) > 15 Then Exit Function
    If s Like "*[!0-9.-]*" Then Exit Function
    If Len(s) - Len(Replace(s, ".", "")) > 1 Then Exit Function
    If InStr(2, s, "-") > 0 Then Exit Function
    Dim t As String
    t = Replace(s, "-", "")
    If Len(t) = 0 Or Left$(t, 1) = "." Or Right$(t, 1) = "." Then Exit Function
    If Len(t) > 1 And Left$(t, 1) = "0" And Mid$(t, 2, 1) <> "." Then Exit Function
    LaSoThuan = True
End Function

Private Function CatChoVuaO(ByVal s As String) As String
    If Len(s) > GIOI_HAN_O Then
        CatChoVuaO = Left$(s, GIOI_HAN_O - 20) & " [...con nua]"
    Else
        CatChoVuaO = s
    End If
End Function

Private Function DangMoFunctionWizard() As Boolean
    On Error Resume Next
    DangMoFunctionWizard = Not Application.CommandBars("Standard").Controls(1).Enabled
End Function

' Chuoi VBA (UTF-16) -> byte UTF-8 (khong BOM) de gui tieng Viet dung.
Private Function Utf8Bytes(ByVal s As String) As Byte()
    Dim st As Object
    Set st = CreateObject("ADODB.Stream")
    st.Type = 2: st.Charset = "utf-8": st.Open
    st.WriteText s
    st.Position = 0: st.Type = 1
    st.Position = 3                       ' bo 3 byte BOM
    Utf8Bytes = st.Read
    st.Close
End Function

Private Function Utf8Text(ByVal b As Variant) As String
    On Error GoTo Rong
    Dim st As Object
    Set st = CreateObject("ADODB.Stream")
    st.Type = 1: st.Open
    st.Write b
    st.Position = 0: st.Type = 2: st.Charset = "utf-8"
    Utf8Text = st.ReadText
    st.Close
    Exit Function
Rong:
    Utf8Text = ""
End Function

Private Function JsonEsc(ByVal s As String) As String
    Dim i As Long, ch As String, code As Long, out As String
    out = Replace(s, "\", "\\")
    out = Replace(out, """", "\""")
    out = Replace(out, vbCrLf, "\n")
    out = Replace(out, vbCr, "\n")
    out = Replace(out, vbLf, "\n")
    out = Replace(out, vbTab, "\t")
    ' Cac ky tu dieu khien con lai
    For code = 0 To 31
        If code <> 9 And code <> 10 And code <> 13 Then
            ch = Chr$(code)
            If InStr(out, ch) > 0 Then out = Replace(out, ch, "\u" & Right$("000" & Hex$(code), 4))
        End If
    Next code
    JsonEsc = out
End Function

'==============================================================================
'                 BO DOC JSON NHO (Dictionary / Collection)
'==============================================================================

Private Function ParseJson(ByVal s As String) As Object
    mJ = s
    mP = 1
    SkipWs
    If Mid$(mJ, mP, 1) = "{" Then
        Set ParseJson = ParseObject()
    ElseIf Mid$(mJ, mP, 1) = "[" Then
        Set ParseJson = ParseArray()
    Else
        Err.Raise vbObjectError + 400, APP_NAME, "Phan hoi khong phai JSON"
    End If
End Function

Private Function ParseValue() As Variant
    SkipWs
    Select Case Mid$(mJ, mP, 1)
        Case "{": Set ParseValue = ParseObject()
        Case "[": Set ParseValue = ParseArray()
        Case """": ParseValue = ParseString()
        Case "t": mP = mP + 4: ParseValue = True
        Case "f": mP = mP + 5: ParseValue = False
        Case "n": mP = mP + 4: ParseValue = Null
        Case Else: ParseValue = ParseNumber()
    End Select
End Function

Private Function LaContainer() As Boolean
    SkipWs
    Dim c As String
    c = Mid$(mJ, mP, 1)
    LaContainer = (c = "{" Or c = "[")
End Function

Private Function ParseObject() As Object
    Dim d As Object, k As String, c As String
    Set d = CreateObject("Scripting.Dictionary")
    mP = mP + 1
    SkipWs
    If Mid$(mJ, mP, 1) = "}" Then
        mP = mP + 1
        Set ParseObject = d
        Exit Function
    End If
    Do
        SkipWs
        k = ParseString()
        SkipWs
        mP = mP + 1                       ' dau :
        If LaContainer() Then
            Set d(k) = ParseValue()
        Else
            d(k) = ParseValue()
        End If
        SkipWs
        c = Mid$(mJ, mP, 1)
        mP = mP + 1
        If c = "}" Then Exit Do
        If c <> "," Then Err.Raise vbObjectError + 401, APP_NAME, "JSON loi tai vi tri " & mP
    Loop
    Set ParseObject = d
End Function

Private Function ParseArray() As Collection
    Dim col As New Collection, c As String
    mP = mP + 1
    SkipWs
    If Mid$(mJ, mP, 1) = "]" Then
        mP = mP + 1
        Set ParseArray = col
        Exit Function
    End If
    Do
        col.Add ParseValue()
        SkipWs
        c = Mid$(mJ, mP, 1)
        mP = mP + 1
        If c = "]" Then Exit Do
        If c <> "," Then Err.Raise vbObjectError + 402, APP_NAME, "JSON loi tai vi tri " & mP
    Loop
    Set ParseArray = col
End Function

Private Function ParseString() As String
    Dim out As String, q As Long, b As Long, e As String, buoc As Long
    mP = mP + 1                           ' dau " mo
    Do
        q = InStr(mP, mJ, """")
        If q = 0 Then Err.Raise vbObjectError + 403, APP_NAME, "JSON thieu dau ngoac kep"
        b = InStr(mP, mJ, "\")
        If b = 0 Or q < b Then
            out = out & Mid$(mJ, mP, q - mP)
            mP = q + 1
            Exit Do
        End If
        out = out & Mid$(mJ, mP, b - mP)
        e = Mid$(mJ, b + 1, 1)
        buoc = 2
        Select Case e
            Case "n": out = out & vbLf
            Case "r": out = out & vbCr
            Case "t": out = out & vbTab
            Case "b": out = out & Chr$(8)
            Case "f": out = out & Chr$(12)
            Case "u"
                out = out & ChrW$(CLng("&H" & Mid$(mJ, b + 2, 4)))
                buoc = 6
            Case Else: out = out & e      ' \" \\ \/
        End Select
        mP = b + buoc
    Loop
    ParseString = out
End Function

Private Function ParseNumber() As Double
    Dim bd As Long
    bd = mP
    Do While mP <= Len(mJ) And InStr("+-0123456789.eE", Mid$(mJ, mP, 1)) > 0
        mP = mP + 1
    Loop
    ParseNumber = Val(Mid$(mJ, bd, mP - bd))
End Function

Private Sub SkipWs()
    Do While mP <= Len(mJ)
        Select Case Mid$(mJ, mP, 1)
            Case " ", vbTab, vbCr, vbLf: mP = mP + 1
            Case Else: Exit Do
        End Select
    Loop
End Sub
