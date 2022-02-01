$(document).ready(function(){
    $(".notification-popup").delay(5000).slideUp(300);

    $('#createClass').click(function (e) {

        var classDay = [];
        $('.day').each(function(){
            if($(this).is(":checked")) {
                classDay.push($(this).val());
            }
        });

        classDay = classDay.toString();

        $.ajax({
            url : '/create-class',
            type : 'POST',
            data : {
                className : $('#className').val(),
                classDesc : $('#classDesc').val(),
                classColor : $('#classColor').val(),
                classTimeStart : $('#classTimeStart').val(),
                classTimeEnd : $('#classTimeEnd').val(),
                classDay : classDay
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#className').val('');
                $('#classDesc').val('');
                $('#classColor').val('#000000');
                $('#classTimeStart').val('');
                $('#classTimeEnd').val('');
                $('.day').prop('checked', false);
                $('.class-wrapper').load(location.href + " .class-wrapper");
                $('#btnCloseClass').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#joinClass').click(function (e) {
        $.ajax({
            url : '/join-class',
            type : 'POST',
            data : {
                classID : $('#classID').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('.class-wrapper').load(location.href + " .class-wrapper");
                $('#classID').val('');
                $('#btnCloseClass').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#updateProfile').click(function (e) {
        $.ajax({
            url : '/edit-profile',
            type : 'POST',
            data : {
                fullname : $('#fullname').val(),
                email : $('#email').val(),
                username : $('#username').val()
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('.details-wrapper').load(location.href + " .details-wrapper");
                $('#btnCloseEditProfile').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#confirmType').click(function (e) {
        $.ajax({
            url : '/change-type',
            type : 'POST',
            data : {
                type : $('#type').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#btnCloseChangeType').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
                $('.details-wrapper').load(location.href + " .details-wrapper");
            }
        });
        e.preventDefault();
    }); 

    $('#updatePassword').click(function (e) {
        $.ajax({
            url : '/change-password',
            type : 'POST',
            data : {
                password : $('#password').val(),
                newPassword : $('#newPassword').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('.details-wrapper').load(location.href + " .details-wrapper");
                $('#btnCloseChangePassword').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    }); 

    $('#delete').click(function (e) {
        $.ajax({
            url : '/delete-account',
            type : 'POST',
            data : {
                password : $('#da-password').val()
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                window.location = "sign_in";
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#addProductiveApp').click(function (e) {
        $.ajax({
            url : '/add-productive-app',
            type : 'POST',
            data : {
                productiveApp : $('#productive-app').val()
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#productive-app').val('');
                $('.list-card').load(location.href + " .list-card");
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#updateClass').click(function (e) {

        var classDay = [];
        $('.day').each(function(){
            if($(this).is(":checked")) {
                classDay.push($(this).val());
            }
        });

        classDay = classDay.toString();

        $.ajax({
            url : '/edit-class',
            type : 'POST',
            data : {
                className : $('#className').val(),
                classDesc : $('#classDesc').val(),
                classColor : $('#classColor').val(),
                classTimeStart : $('#classTimeStart').val(),
                classTimeEnd : $('#classTimeEnd').val(),
                classDay : classDay
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('.class-wrapper').load(location.href + " .class-wrapper");
                $('#btnCloseEditClass').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#addWebBlock').click(function (e) {
        $.ajax({
            url : '/add-web-block',
            type : 'POST',
            data : {
                blockName : $('#webURL').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#cancelInputWeb').click();
                $('#webURL').val('');
                $('.web-checkbox').load(location.href + " .web-checkbox");
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#addAppBlock').click(function (e) {
        $.ajax({
            url : '/add-app-block',
            type : 'POST',
            data : {
                blockName : $('#appName').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#cancelInputApp').click();
                $('#appName').val('');
                $('.app-checkbox').load(location.href + " .app-checkbox");
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });


    $('#saveWebBlock').click(function (e) {

        var webBlock = [];
        $('.web-lists').each(function(){
            if($(this).is(":checked")) {
                webBlock.push($(this).val());
            }
        });

        webBlock = webBlock.toString();

        $.ajax({
            url : '/save-web-block',
            type : 'POST',
            data : {
                webBlock : webBlock
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#btnCloseWeb').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#saveAppBlock').click(function (e) {

        var appBlock = [];
        $('.app-lists').each(function(){
            if($(this).is(":checked")) {
                appBlock.push($(this).val());
            }
        });

        appBlock = appBlock.toString();

        $.ajax({
            url : '/save-app-block',
            type : 'POST',
            data : {
                appBlock : appBlock
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#btnCloseApp').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });  

    $('#saveTrackConfig').click (function (e) {
        var blocker = [];
        var kbLimit = [];
        var idle = [];
        
        $('.blocker').each(function(){
            if($(this).is(":checked")) {
                blocker.push($(this).val());
            }
        });
        $('.kbLimit').each(function(){
            if($(this).is(":checked")) {
                kbLimit.push($(this).val());
            }
        });
        $('.idle').each(function(){
            if($(this).is(":checked")) {
                idle.push($(this).val());
            }
        });
        blocker = blocker.toString();
        kbLimit = kbLimit.toString();
        idle = idle.toString();
        $.ajax({
            url : '/save-tracker-config',
            type : 'POST',
            data : {
                numOfIdle : $('#numOfIdle').val(),
                blocker : blocker,
                kbLimit : kbLimit,
                idle : idle
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#btnCloseTracker').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });

    $('#addUser').click(function (e) {
        usertype = $('#type').val().toString()
        $.ajax({
            url : '/admin/add-user',
            type : 'POST',
            data : {
                usertype : usertype,
                fullname : $('#fullname').val(),
                email : $('#email').val(),
                username : $('#username').val(),
                password : $('#password').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#btnCloseUser').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });  
    
    $('#gridView').click(function (e) {
        $.ajax({
            url : '/grid-view',
            type : 'POST',
            data : {
                gridValue : $('#gridValue').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                console.log('error')
            }
            else {
                $('#wrapper').load(location.href + " #wrapper");
            }
        });
        e.preventDefault();
    }); 

    $('#listView').click(function (e) {
        $.ajax({
            url : '/list-view',
            type : 'POST',
            data : {
                listValue : $('#listValue').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                console.log('error')
            }
            else {
                $('#wrapper').load(location.href + " #wrapper");
            }
        });
        e.preventDefault();
    }); 
    
    $('#publishBtn').click(function (e) {
        $.ajax({
            url : '/publish-class',
            type : 'POST',
            data : {
                publishValue : $('#publishValue').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                console.log('error')
            }
            else {
                $('.class-settings-wrapper').load(location.href + " .class-settings-wrapper");
                $('.class-subpage').load(location.href + " .class-subpage");
            }
        });
        e.preventDefault();
    }); 

    $('#unpublishBtn').click(function (e) {
        $.ajax({
            url : '/unpublish-class',
            type : 'POST',
            data : {
                unpublishValue : $('#unpublishValue').val(),
            }
        })
        .done(function(data) {
            if (data.error) {
                console.log('error')
            }
            else {
                $('.class-settings-wrapper').load(location.href + " .class-settings-wrapper");
            }
        });
        e.preventDefault();
    }); 


    $('#createClassadmin').click(function (e) {
        var classDay = [];
        $('.day').each(function(){
            if($(this).is(":checked")) {
                classDay.push($(this).val());
            }
        });

        classDay = classDay.toString();

        $.ajax({
            url : '/admin/class/add',
            type : 'POST',
            data : {
                className : $('#className').val(),
                classDesc : $('#classDesc').val(),
                classColor : $('#classColor').val(),
                instructor : $('#instructor').val().toString(),
                classTimeStart : $('#classTimeStart').val(),
                classTimeEnd : $('#classTimeEnd').val(),
                classDay : classDay
            }
        })
        .done(function(data) {
            if (data.error) {
                $('#errorAlert').text(data.error).show().delay(5000).slideUp(300);
            }
            else {
                $('#className').val('');
                $('#classDesc').val('');
                $('#classColor').val('#000000');
                $('#classTimeStart').val('');
                $('#classTimeEnd').val('');
                $('.day').prop('checked', false);
                $('.user-table').load(location.href + " .user-table");
                $('#btnCloseClass').click();
                $('#successAlert').text(data.msg).show().delay(5000).slideUp(300);
            }
        });
        e.preventDefault();
    });
});